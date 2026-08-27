src/tts_cli/
├── core/
│   ├── models.py
│   ├── interfaces.py
│   ├── capabilities.py
│   ├── errors.py
│   └── config.py
│
├── application/
│   ├── synthesize.py
│   ├── transcribe.py
│   ├── batch_process.py
│   └── voice_listing.py
│
├── providers/
│   ├── tts/
│   │   ├── edge.py
│   │   ├── google.py
│   │   └── factory.py
│   ├── stt/
│   │   ├── whisper.py
│   │   └── factory.py
│   └── media/
│       ├── ffmpeg.py
│       └── probe.py
│
├── input/
│   ├── processor.py
│   ├── readers.py
│   └── resolver.py
│
├── subtitle/
│   ├── cues.py
│   └── srt.py
│
├── output/
│   ├── formats.py
│   ├── resolver.py
│   └── project.py
│
├── cli/
│   ├── commands.py
│   └── parser.py
│
└── services/
    └── voices.py


## Trạng thái hiện tại

| Khu vực | Trạng thái | Ghi chú |
| --- | --- | --- |
| Folder structure | Hoàn chỉnh | Đã có `core`, `application`, `providers/tts`, `providers/stt`, `providers/media`, `input`, `subtitle`, `output`, `cli` và `services`. |
| TTS application flow | Hoàn chỉnh | `SynthesizeUseCase` xử lý normalize, retry, subtitle và output. |
| Edge provider | Hoàn chỉnh | Có streaming audio và `WordBoundary`; trả về `SynthesisResult`. |
| Google TTS provider | Hoàn chỉnh có giới hạn | Tạo MP3 qua Google Cloud TTS; provider không cung cấp word timing nên cues có thể rỗng. |
| Input TXT/SRT/VTT | Hoàn chỉnh | Reader và resolver đã nằm trực tiếp trong `input/`. |
| Batch flow | Hoàn chỉnh | `BatchProcessUseCase` hỗ trợ recursive, skip-existing và continue-on-error. |
| Media FFmpeg adapter | Hoàn chỉnh | Có extract audio và probe metadata. |
| STT provider | Hoàn chỉnh | Có `WhisperTranscriber` và đăng ký trong `STTProviderFactory`. |
| CLI transcription | Hoàn chỉnh | Có command `transcribe` cho audio/video và các tùy chọn Whisper. |
| Core result/capability model | Hoàn chỉnh | `SynthesisResult`, `TranscriptResult`, `ProviderCapabilities` đã được dùng trong runtime. |
| Test structure | Hoàn chỉnh | Toàn bộ 64 test pass; import, API use-case và assertion đã đồng bộ với cấu trúc mới. |
| Documentation | Hoàn chỉnh | README đã mô tả Google TTS, transcription, Whisper/FFmpeg và giới hạn timing của Google. |
| Tuân thủ đầy đủ mục 2 | Hoàn chỉnh | Runtime, test structure và documentation đã đồng bộ với cấu trúc mục 2. |

## Kiểm tra đã thực hiện

1. Test nhóm migration: `19 passed`.
2. Test transcription: `1 passed`.
3. Toàn bộ test suite: `64 passed`.
4. Quét test không còn `tts_cli.text`, `services.tts`, `services.batch`, `services.edge_tts_engine`, `.generate()`, `.process()` hoặc `TTSService`.

