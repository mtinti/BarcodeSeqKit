BarcodeSeqKit
================

<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

## Overview

BarcodeSeqKit is a Python library for extracting and classifying
sequencing reads based on the presence of specific barcode sequences. It
supports both BAM and FASTQ file formats and provides flexible options
for barcode matching and output generation.

## Installation

You can install the package via pip:

``` bash
pip install barcodeseqkit
```

Or directly from the repository:

``` bash
pip install git+https://github.com/username/BarcodeSeqKit.git
```

## Usage

BarcodeSeqKit can be used as a Python library or as a command-line tool.
Below, we’ll demonstrate both usage patterns.

### Command-line Usage

BarcodeSeqKit provides a command-line interface through the
`barcodeseqkit` command. Here are the basic arguments:

    usage: barcodeseqkit [-h] [--bam BAM | --fastq1 FASTQ1 | --fastq-dir FASTQ_DIR] [--fastq2 FASTQ2]
                           [--barcode-config BARCODE_CONFIG | --barcode BARCODE | --barcode5 BARCODE5] [--barcode3 BARCODE3]
                           [--max-mismatches MAX_MISMATCHES] --output-prefix OUTPUT_PREFIX
                           [--output-dir OUTPUT_DIR] [--discard-unmatched] [--search-softclipped]
                           [--search-both-reads] [--verbose] [--log-file LOG_FILE]

#### Single Barcode Example

When you have a single barcode sequence, you can use the `--barcode`
option. This creates two output files with reads matching the barcode in
forward orientation (`barcode_orientFR`) and reverse complement
orientation (`barcode_orientRC`).

Let’s run an example using the test BAM file provided with the package:

``` python
barcodeseqkit --bam ../tests/test.bam \
--barcode CTGACTCCTTAAGGGCC --output-prefix test_out_1 \
--output-dir ../tests/test_out_1
```

This command will: 1. Process the BAM file at `tests/test.bam` 2. Search
for the barcode sequence `CTGACTCCTTAAGGGCC` (and its reverse
complement) 3. Create the following output files in the
`tests/test_out_1` directory: - `test_out_1_barcode_orientFR.bam`: Reads
with the barcode in forward orientation -
`test_out_1_barcode_orientRC.bam`: Reads with the barcode in reverse
complement orientation - `test_out_1_noBarcode.bam`: Reads without the
barcode - `test_out_1_extraction_stats.json` and
`test_out_1_extraction_stats.tsv`: Extraction statistics

#### Dual Barcode Example

When you have two barcode sequences with specific locations (5’ and 3’),
you can use the `--barcode5` and `--barcode3` options. This creates four
output files for all combinations of barcode locations and orientations.

Let’s run an example with both 5’ and 3’ barcodes:

``` python
barcodeseqkit --bam ../tests/test.bam \
--barcode5 CTGACTCCTTAAGGGCC \
--barcode3 TAACTGAGGCCGGC \
--output-prefix test_out_2 --output-dir ../tests/test_out_2
```

This command will: 1. Process the BAM file at `tests/test.bam` 2. Search
for the 5’ barcode sequence `CTGACTCCTTAAGGGCC` and the 3’ barcode
sequence `TAACTGAGGCCGGC` (and their reverse complements) 3. Create the
following output files in the `tests/test_out_2` directory: -
`test_out_2_barcode5_orientFR.bam`: Reads with the 5’ barcode in forward
orientation - `test_out_2_barcode5_orientRC.bam`: Reads with the 5’
barcode in reverse complement orientation -
`test_out_2_barcode3_orientFR.bam`: Reads with the 3’ barcode in forward
orientation - `test_out_2_barcode3_orientRC.bam`: Reads with the 3’
barcode in reverse complement orientation - `test_out_2_noBarcode.bam`:
Reads without any barcode - `test_out_2_extraction_stats.json` and
`test_out_2_extraction_stats.tsv`: Extraction statistics

## Extracting Softclipped Regions from Alignments

> BarcodeSeqKit also includes an option to analyse only the softclipped
> sequences from read alignments.

Barcodes are generally present in softclipped regions of the reads. Also
we can use to look for the splice leader sequence (trypanosomatids).

The
[`extract_softclipped_region`](https://mtinti.github.io/BarcodeSeqKit/bam_processing.html#extract_softclipped_region)
function extracts orientation-specific softclipped sequences: - For
reads on the forward strand (+): extracts the softclipped sequence at
the 5’ end - For reads on the reverse strand (-): extracts the
softclipped sequence at the 3’ end

## Examining Extraction Statistics

Let’s examine the extraction statistics from both examples. First, we’ll
load the necessary libraries:

``` python
import pandas as pd
import json
import os
```

    /Users/MTinti/miniconda3/envs/work3/lib/python3.10/site-packages/pandas/core/arrays/masked.py:60: UserWarning: Pandas requires version '1.3.6' or newer of 'bottleneck' (version '1.3.4' currently installed).
      from pandas.core import (

### Single Barcode Statistics

Let’s load and display the statistics for the single barcode example:

``` python
df = pd.read_csv('../tests/test_out_1/test_out_1_extraction_stats.tsv',sep='\t')
df
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Metric</th>
      <th>Value</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>TotalReads</td>
      <td>498</td>
    </tr>
    <tr>
      <th>1</th>
      <td>TotalBarcodeMatches</td>
      <td>10</td>
    </tr>
    <tr>
      <th>2</th>
      <td>NoBarcodeCount</td>
      <td>481</td>
    </tr>
    <tr>
      <th>3</th>
      <td>MatchRate</td>
      <td>0.0201</td>
    </tr>
    <tr>
      <th>4</th>
      <td>Barcode</td>
      <td>Count</td>
    </tr>
    <tr>
      <th>5</th>
      <td>generic</td>
      <td>10</td>
    </tr>
    <tr>
      <th>6</th>
      <td>Orientation</td>
      <td>Count</td>
    </tr>
    <tr>
      <th>7</th>
      <td>FR</td>
      <td>7</td>
    </tr>
    <tr>
      <th>8</th>
      <td>RC</td>
      <td>3</td>
    </tr>
    <tr>
      <th>9</th>
      <td>Category</td>
      <td>Count</td>
    </tr>
    <tr>
      <th>10</th>
      <td>barcode_orientFR</td>
      <td>7</td>
    </tr>
    <tr>
      <th>11</th>
      <td>barcode_orientRC</td>
      <td>3</td>
    </tr>
  </tbody>
</table>
</div>

### Dual Barcode Statistics

Now let’s examine the statistics for the dual barcode example:

``` python
df = pd.read_csv('../tests/test_out_2/test_out_2_extraction_stats.tsv',sep='\t')
df
```

<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Metric</th>
      <th>Value</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>TotalReads</td>
      <td>498</td>
    </tr>
    <tr>
      <th>1</th>
      <td>TotalBarcodeMatches</td>
      <td>18</td>
    </tr>
    <tr>
      <th>2</th>
      <td>NoBarcodeCount</td>
      <td>470</td>
    </tr>
    <tr>
      <th>3</th>
      <td>MatchRate</td>
      <td>0.0361</td>
    </tr>
    <tr>
      <th>4</th>
      <td>Barcode</td>
      <td>Count</td>
    </tr>
    <tr>
      <th>5</th>
      <td>5</td>
      <td>10</td>
    </tr>
    <tr>
      <th>6</th>
      <td>3</td>
      <td>8</td>
    </tr>
    <tr>
      <th>7</th>
      <td>Orientation</td>
      <td>Count</td>
    </tr>
    <tr>
      <th>8</th>
      <td>FR</td>
      <td>10</td>
    </tr>
    <tr>
      <th>9</th>
      <td>RC</td>
      <td>8</td>
    </tr>
    <tr>
      <th>10</th>
      <td>Category</td>
      <td>Count</td>
    </tr>
    <tr>
      <th>11</th>
      <td>barcode5_orientFR</td>
      <td>7</td>
    </tr>
    <tr>
      <th>12</th>
      <td>barcode3_orientFR</td>
      <td>3</td>
    </tr>
    <tr>
      <th>13</th>
      <td>barcode3_orientRC</td>
      <td>5</td>
    </tr>
    <tr>
      <th>14</th>
      <td>barcode5_orientRC</td>
      <td>3</td>
    </tr>
  </tbody>
</table>
</div>

## Programmatic Usage

You can also use BarcodeSeqKit programmatically in your Python code.
Here’s an example:

## Bam file

``` python
from BarcodeSeqKit.core import BarcodeConfig, ExtractorConfig, ExtractorFactory, BarcodeLocationType

# Define barcode configurations
barcode5 = BarcodeConfig(
    sequence="CTGACTCCTTAAGGGCC",
    location=BarcodeLocationType.FIVE_PRIME,
    name="5",
    description="5' barcode sequence"
)

barcode3 = BarcodeConfig(
    sequence="TAACTGAGGCCGGC",
    location=BarcodeLocationType.THREE_PRIME,
    name="3",
    description="3' barcode sequence"
)

# Create extractor configuration
config = ExtractorConfig(
    barcodes=[barcode5, barcode3],
    output_prefix="programmatic_example",
    output_dir="../tests/programmatic_out",
    keep_unmatched=True,
    verbose=True,
    #search_softclipped=True
    
    
)
# Create the extractor
extractor = ExtractorFactory.create_extractor(config, "../tests/test.bam")
stats = extractor.extract()
print(f"Extraction complete: {stats.total_barcode_matches} matches in {stats.total_reads} aligments")
#extractor
```

    2025-03-14 10:45:14,191 - BarcodeSeqKit - INFO - Extraction complete: 18 matches in 498 reads
    2025-03-14 10:45:14,317 - BarcodeSeqKit - INFO - Statistics saved to ../tests/programmatic_out/programmatic_example_extraction_stats.json and ../tests/programmatic_out/programmatic_example_extraction_stats.tsv

    Extraction complete: 18 matches in 498 aligments

## Fastq paired file

``` python
# Initialize the extractor Extraction complete: 18 matches in 498 aligments
from BarcodeSeqKit.fastq_processing import FastqExtractor
extractor = FastqExtractor(
    barcodes=[barcode5, barcode3],
    output_prefix="res",
    fastq_files=['../tests/test.1.fastq.gz', '../tests/test.2.fastq.gz'],
    output_dir='../tests/programmatic_out_fastq',
    verbose=True
)
stats = extractor.extract()
# Run extraction (commented out to avoid running it by default)
#stats = extractor.extract()
print(f"Extraction complete: {stats.total_barcode_matches} matches in {stats.total_reads} reads")
```

    0it [00:00, ?it/s]

    2025-03-14 10:45:14,491 - BarcodeSeqKit - INFO - Statistics saved to ../tests/programmatic_out_fastq/res_extraction_stats.json and ../tests/programmatic_out_fastq/res_extraction_stats.tsv
    2025-03-14 10:45:14,491 - BarcodeSeqKit - INFO - Statistics saved to ../tests/programmatic_out_fastq/res_extraction_stats.json and ../tests/programmatic_out_fastq/res_extraction_stats.tsv

    Extraction complete: 18 matches in 247 reads

## Advanced Options

BarcodeSeqKit provides several advanced options for barcode extraction:

- **Fuzzy matching**: Use `--max-mismatches` to allow a specific number
  of mismatches in barcode detection.
- **Paired-end FASTQ files**: Use `--fastq1` and `--fastq2` to process
  paired-end FASTQ files.
- **Discarding unmatched reads**: Use `--discard-unmatched` to exclude
  reads without barcode matches from the output.

For more options, run `barcodeseqkit --help`.

## Conclusion

BarcodeSeqKit provides a flexible and efficient way to extract and
classify sequences based on barcode presence. Whether you’re working
with BAM or FASTQ files, single or multiple barcodes, BarcodeSeqKit
offers a straightforward interface for your barcode extraction needs.
