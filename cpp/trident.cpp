#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <iostream>
#include <algorithm>
#include <unordered_map>

namespace py = pybind11;

static inline std::string trim(const std::string& s) {
    size_t b = 0, e = s.size();
    while (b < e && std::isspace(static_cast<unsigned char>(s[b]))) ++b;
    while (e > b && std::isspace(static_cast<unsigned char>(s[e-1]))) --e;
    return s.substr(b, e-b);
}

static inline bool parse_float(const std::string& s, float& out) {
    char* end = nullptr;
    const char* c = s.c_str();
    errno = 0;
    float v = std::strtof(c, &end);
    if (errno == ERANGE) return false;
    while (end && *end && std::isspace(static_cast<unsigned char>(*end))) ++end;
    if (!end || *end != '\0') return false;
    out = v;
    return true;
}

static inline std::string strip_quotes(const std::string& s) {
    if (s.size() >= 2 && s.front() == '"' && s.back() == '"')
        return s.substr(1, s.size() - 2);
    return s;
}

std::vector<std::string> parse_csv_line(const std::string& line) {
    std::vector<std::string> fields;
    std::string field;
    bool in_quotes = false;
    
    for (size_t i = 0; i < line.length(); ++i) {
        char c = line[i];
        if (c == '"') {
            in_quotes = !in_quotes;
        } else if (c == ',' && !in_quotes) {
            fields.push_back(trim(field));
            field.clear();
        } else {
            field += c;
        }
    }
    fields.push_back(trim(field));
    return fields;
}

class TRIDENTDataLoader {
public:
    // Returns (numpy.float32 array [rows, cols], list[dict] mappings, list[bool] is_categorical)
    py::tuple load_csv(const std::string& filepath,
                       const std::vector<std::string>& labels = {}) {
        std::ifstream file(filepath);
        if (!file.is_open()) {
            throw std::runtime_error("Cannot open file: " + filepath);
        }

        std::string line;
        if (!std::getline(file, line)) {
            throw std::runtime_error("CSV file is empty: " + filepath);
        }

        // Parse the header first and map it
        std::vector<std::string> headers = parse_csv_line(line);
        std::unordered_map<std::string, size_t> header_map;
        for (size_t i = 0; i < headers.size(); ++i) header_map[headers[i]] = i;

        // Pick columns based on selected labels
        std::vector<size_t> col_indices;
        if (!labels.empty()) {
            std::cout << "[DEBUG] Looking for labels: ";
            for (const auto& lbl : labels) std::cout << "'" << lbl << "' ";
            std::cout << "\n";
            
            for (const auto& lbl : labels) {
                auto it = header_map.find(lbl);
                if (it == header_map.end()) {
                    std::cout << "[DEBUG] Label '" << lbl << "' not found in headers!\n";
                    throw std::runtime_error("Label not found: " + lbl);
                }
                std::cout << "[DEBUG] Label '" << lbl << "' found at column " << it->second << "\n";
                col_indices.push_back(it->second);
            }
        } else {
            for (size_t i = 0; i < headers.size(); ++i) col_indices.push_back(i);
        }
        
        std::cout << "[DEBUG] Selected column indices: ";
        for (auto idx : col_indices) std::cout << idx << " ";
        std::cout << "\n";
        
        std::cout << "[DEBUG] Selected column names: ";
        for (auto idx : col_indices) std::cout << "'" << headers[idx] << "' ";
        std::cout << "\n";
        const size_t out_cols = col_indices.size();

        // Read all rows as strings
        std::vector<std::vector<std::string>> rows_str;
        while (std::getline(file, line)) {
            if (line.empty()) continue;
            auto cells = parse_csv_line(line);
            
            // Project parsed fields to selected columns
            std::vector<std::string> proj(out_cols);
            for (size_t j = 0; j < out_cols; ++j) {
                size_t col = col_indices[j];
                proj[j] = (col < cells.size() ? cells[col] : "");
            }
            rows_str.emplace_back(std::move(proj));
        }
        if (rows_str.empty()) {
            throw std::runtime_error("No data rows in CSV file");
        }
        const size_t out_rows = rows_str.size();

        // Decide per-column: numeric vs categorical
        std::vector<bool> is_categorical(out_cols, false);
        for (size_t j = 0; j < out_cols; ++j) {
            bool numeric = true;
            for (size_t i = 0; i < out_rows; ++i) {
                const std::string& orig = rows_str[i][j];
                std::string s = strip_quotes(orig);  
                if (s.empty()) continue; 
                float tmp;
                if (!parse_float(s, tmp)) { 
                    numeric = false; 
                    std::cout << "[DEBUG] Non-numeric value in column " << j 
                              << " (actual column " << col_indices[j] << ", '" 
                              << headers[col_indices[j]] << "'): '" << s << "'\n";
                    break; 
                }
            }
            is_categorical[j] = !numeric;
        }

        // Build mappings for categorical columns and numeric columns (for potential categorical override)
        std::vector<std::unordered_map<std::string, int>> cat_maps(out_cols);
        const int MAX_CATEGORICAL_VALUES = 1000;
        
        for (size_t j = 0; j < out_cols; ++j) {
            auto& cmap = cat_maps[j];
            
            if (is_categorical[j]) {
                int next_id = 0;
                
                // Collect all non-empty values
                for (size_t i = 0; i < out_rows; ++i) {
                    const std::string& s = rows_str[i][j];
                    if (!s.empty() && cmap.find(s) == cmap.end()) {
                        cmap[s] = next_id++;
                    }
                }
                
                // Check if there are any empty values
                bool has_missing = false;
                for (size_t i = 0; i < out_rows; ++i) {
                    if (rows_str[i][j].empty()) {
                        has_missing = true;
                        break;
                    }
                }
                
                // Only add "nan" if there are missing values
                if (has_missing) {
                    cmap["nan"] = next_id++;
                }
            } else {
                // Numeric column - create mapping for categorical override possibility
                std::unordered_map<std::string, int> value_map;
                int next_id = 0;
                bool overflow = false;
                
                // Collect unique numeric values
                for (size_t i = 0; i < out_rows; ++i) {
                    const std::string& orig = rows_str[i][j];
                    std::string s = strip_quotes(orig);
                    
                    if (s.empty()) continue;
                    
                    float tmp;
                    if (parse_float(s, tmp)) {
                        if (value_map.find(s) == value_map.end()) {
                            if (next_id >= MAX_CATEGORICAL_VALUES) {
                                overflow = true;
                                break;
                            }
                            value_map[s] = next_id++;
                        }
                    }
                }
                
                if (overflow) {
                    std::cout << "[TRIDENT C++] Column " << j << " ('" << headers[col_indices[j]] 
                              << "') has >" << MAX_CATEGORICAL_VALUES 
                              << " unique values (threshold exceeded). Marking as overflow.\n";
                    cmap.clear();
                    cmap["Overflow"] = -1;
                    cmap["Too Many"] = -2;
                } else if (next_id > 0) {
                    std::cout << "[TRIDENT C++] Column " << j << " ('" << headers[col_indices[j]] 
                              << "') has " << next_id << " unique numeric values. Creating mapping for potential categorical override.\n";
                    cmap = std::move(value_map);
                    
                    // Check for missing values
                    bool has_missing = false;
                    for (size_t i = 0; i < out_rows; ++i) {
                        const std::string& orig = rows_str[i][j];
                        std::string s = strip_quotes(orig);
                        if (s.empty()) {
                            has_missing = true;
                            break;
                        }
                    }
                    
                    if (has_missing) {
                        cmap["nan"] = next_id++;
                    }
                }
            }
        }

        // Allocate result array
        auto result = py::array_t<float>({out_rows, out_cols},
                                         {sizeof(float)*out_cols, sizeof(float)});
        auto buf = result.request();
        float* ptr = static_cast<float*>(buf.ptr);
        const float NaN = std::numeric_limits<float>::quiet_NaN();

        // Fill array
        for (size_t i = 0; i < out_rows; ++i) {
            for (size_t j = 0; j < out_cols; ++j) {
                float v = NaN;
                const std::string& orig = rows_str[i][j];
                std::string s = strip_quotes(orig);
                
                if (is_categorical[j]) {
                    const auto& cmap = cat_maps[j];
                    if (s.empty()) {
                        auto nan_it = cmap.find("nan");
                        v = (nan_it != cmap.end()) ? static_cast<float>(nan_it->second) : NaN;
                    } else {
                        auto it = cmap.find(orig);
                        v = (it == cmap.end()) ? NaN : static_cast<float>(it->second);
                    }
                } else {
                    // Numeric columns
                    if (s.empty()) {
                        v = NaN;
                    } else {
                        if (!parse_float(s, v)) {
                            v = NaN;
                        }
                    }
                }
                ptr[i*out_cols + j] = v;
            }
        }

        // Build Python-side mappings and flags
        py::list py_maps;
        for (size_t j = 0; j < out_cols; ++j) {
            if (cat_maps[j].empty()) {
                py_maps.append(py::none());
            } else if (cat_maps[j].size() == 2 && 
                       cat_maps[j].find("Overflow") != cat_maps[j].end() &&
                       cat_maps[j].find("Too Many") != cat_maps[j].end()) {
                py::dict d;
                d[py::str("Overflow")] = py::str("Too Many");
                py_maps.append(std::move(d));
            } else {
                py::dict d;
                for (const auto& kv : cat_maps[j]) {
                    d[py::str(kv.first)] = py::int_(kv.second);
                }
                py_maps.append(std::move(d));
            }
        }

        py::list py_is_cat;
        for (bool b : is_categorical) py_is_cat.append(py::bool_(b));

        std::cout << "[TRIDENT C++] Loaded CSV (rows=" << out_rows
                  << ", cols=" << out_cols << ")\n";

        // return (array, mappings, is_categorical)
        return py::make_tuple(result, py_maps, py_is_cat);
    }

    // Getter for shape
    std::tuple<size_t, size_t> get_shape(py::array_t<float> array) {
        auto buf = array.request();
        return std::make_tuple(buf.shape[0], buf.shape[1]);
    }

    py::array_t<float> merge_data(py::array_t<float> data, py::array_t<float> obs) {
        // Get shapes
        auto data_buf = data.request();
        auto obs_buf = obs.request();

        if (data_buf.shape[0] != obs_buf.shape[0]) {
            throw std::runtime_error("Incompatible array shapes: different number of rows");
        }

        size_t rows = data_buf.shape[0];
        size_t data_cols = data_buf.shape[1];
        size_t obs_cols = obs_buf.shape[1];
        size_t merged_cols = data_cols + obs_cols;

        // Create merged array
        py::array_t<float> merged({rows, merged_cols});
        auto merged_buf = merged.request();
        float* merged_ptr = static_cast<float*>(merged_buf.ptr);

        const float* data_ptr = static_cast<const float*>(data_buf.ptr);
        const float* obs_ptr = static_cast<const float*>(obs_buf.ptr);

        // Copy row by row
        for (size_t i = 0; i < rows; ++i) {
            // Copy data row
            std::memcpy(
                merged_ptr + i * merged_cols,
                data_ptr + i * data_cols,
                data_cols * sizeof(float)
            );
            // Copy obs row
            std::memcpy(
                merged_ptr + i * merged_cols + data_cols,
                obs_ptr + i * obs_cols,
                obs_cols * sizeof(float)
            );
        }

        return merged;
    }
};

PYBIND11_MODULE(_trident, m) {
    m.doc() = "TRIDENT core - High performance data processing";

    py::class_<TRIDENTDataLoader>(m, "DataLoader")
    .def(py::init<>())
    .def("load_csv", &TRIDENTDataLoader::load_csv,
         py::arg("filepath"),
         py::arg("labels") = std::vector<std::string>(),
         "Load CSV file and return numpy array, optionally filtering columns by labels")
    .def("get_shape", &TRIDENTDataLoader::get_shape, "Get shape of numpy array")
    .def("merge_data", &TRIDENTDataLoader::merge_data,
         py::arg("data"),
         py::arg("obs"),
         "Merge two arrays horizontally (columns).");
}