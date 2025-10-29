<p align="center">
  <img src=".github\others\logo.png" alt="TRIDENT">
</p>

# TRIDENT (Tri-Dimensional Embeddings Navigation Tool)

**TRIDENT** is a Blender add-on for generating 3D visualizations from dimensionality-reduced data such as UMAP, t-SNE, and PCA. It uses the EEVEE rendering engine for real-time navigation, category-based color labeling, and export of publication-grade images or animation frames.

---

## Overview

TRIDENT transforms Blender into a scientific visualization environment. You can import embeddings from CSV files, render them as point clouds, assign category labels, and capture high-quality figures or animations directly within Blender’s interface.

---

## Features

### Data Import and Setup

TRIDENT reads CSV files where each row represents a data point in reduced-dimensional space.

Supports:

- XYZ coordinates (UMAP, t-SNE, PCA, etc.)
- Optional metadata columns for labels or grouping

### Interactive 3D Exploration

After import, TRIDENT plots your data directly in the Blender viewport using the **EEVEE** renderer.

You can:

- Navigate freely through data clusters
- Toggle categories or classes on and off
- Adjust transparency and palettes

### Scientific Visualization in Blender

TRIDENT turns Blender into a figure-generation tool.

You can:

- Export **publication-ready stills**
- Render **camera flythroughs**
- Reuse **lighting and material presets**

## Installation

To install TRIDENT, first download the release that matches your system directly from inside Blender from **Edit → Preferences → Get Extensions**, then search for **TRIDENT**. Or from the link below:

**Blender Extensions: [Download TRIDENT](https://extensions.blender.org/add-ons/trident/)**


Alternatively, it can be downloaded from here following the instructions.
Github Releases: [Download TRIDENT (Not Recommended)](https://github.com/c-cordi/TRIDENT/releases)

Open Blender and go to **Edit → Preferences → Get Extensions**, then click **Install from disk...** from the menu on the top right arrow. Select the downloaded `.zip` file. After the add-on is installed, simply enable it by checking the box next to **TRIDENT** in the add-ons list.

---

## Usage

Once installed, TRIDENT will be available in Blender’s sidebar (Press "N" to pop the sidebar).

For usage instructions and further tips, refer to the [Wiki](https://github.com/c-cordi/TRIDENT/wiki) page.

---

## Requirements

TRIDENT requires [Blender](https://www.blender.org/) version 4.2 or higher. All necessary Python dependencies are bundled with the add-on, so no extra installation steps are needed.

---

## Roadmap

Planned additions:

- Metadata inspection by clicking individual clusters
- Custom legend formatting
- Filtering and masking tools for focused analysis
- Layout presets for multi-panel figure composition

---

## License

This project is distributed under the GPL License.
