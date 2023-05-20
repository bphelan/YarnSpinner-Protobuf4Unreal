# YarnSpinner: Protobuf for Unreal

This repo hosts the protobuf library and `.proto` file builders for the [YarnSpinner Unreal Engine plugin](https://github.com/YarnSpinnerTool/YarnSpinner-Unreal).  It can be used to build/update protobuf or to generate Unreal-compatible versions of the compiled YarnSpinner protobuf files.


## Prerequisites

All platforms require the following to be available in `PATH`:
- python >= 3.2
- git >= 2.25
- cmake >= v3.20

The tool also expects a local clone of
[YarnSpinner-Unreal](https://github.com/YarnSpinnerTool/YarnSpinner-Unreal) to deploy built artifacts into.


### Windows-specific

- Visual Studio 2019

### Mac-specific

- Xcode

## Usage

```sh
python build.py --plugin_path ../path/to/YarnSpinner-Unreal/
```

