# Skrivist Calibre Plugin

Send books from Calibre directly to your Skriv.ist cloud library.

## Installation

1. Download `skrivist-calibre-plugin.zip`
2. Open Calibre
3. Go to **Preferences** > **Plugins** > **Load plugin from file**
4. Select the downloaded zip file
5. Restart Calibre

## Configuration

1. Go to **Preferences** > **Plugins**
2. Find "Skrivist" under "User interface action"
3. Click **Customize plugin**
4. Enter your Skrivist API key (generate one at skriv.ist/settings)
5. Click **OK**

## Usage

1. Select one or more books in your Calibre library
2. Click the **Send to Skriv** button in the toolbar (or press `Ctrl+Shift+K`)
3. Books will be uploaded to your Skriv.ist cloud library

## Requirements

- Calibre 5.0 or newer
- Books must be in EPUB format
- A Skriv.ist account with an API key

## Building from Source

```bash
cd calibre-plugin
zip -r ../skrivist-calibre-plugin.zip . -x "*.md" -x "*.pyc" -x "__pycache__/*"
```

## Troubleshooting

**"API Key Required" error**
- Make sure you've configured your API key in plugin settings

**"Book is not in EPUB format" error**
- Convert your book to EPUB using Calibre's Convert feature

**Upload fails**
- Check your internet connection
- Verify your API key is valid
- Ensure the server URL is correct (default: https://skriv.ist)
