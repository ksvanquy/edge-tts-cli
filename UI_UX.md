# UI/UX Blueprint Theo Code Thực Tế

**Dự án:** `edge-tts-cli`
**Phiên bản code hiện tại:** `1.0.0`
**Mục đích:** đặc tả giao diện tương lai dựa trên code hiện tại; không mô tả một UI đã được triển khai.

## 0. Audit nguồn sự thật

Tài liệu này được đối chiếu với code hiện tại ngày 2026-08-27. Trạng thái của
từng phần được phân loại như sau:

| Phần | Nguồn code | Trạng thái audit |
| --- | --- | --- |
| Command, option và default CLI | `src/tts_cli/cli/parser.py`, `src/tts_cli/cli/constants.py` | Đã xác nhận |
| Mặc định cấu hình TTS | `src/tts_cli/core/constants.py`, `TTSConfig` | Đã xác nhận |
| Generate | `SynthesizeUseCase`, `TTSProviderFactory`, `OutputResolver` | Đã xác nhận |
| Batch | `BatchProcessUseCase`, `BatchFileService` | Đã xác nhận |
| Transcribe | `TranscribeUseCase`, `TranscribeConfig`, `TranscriptResult` | Đã xác nhận |
| Voices | `VoiceListingUseCase`, `VoiceCatalogService` | Đã xác nhận; output hiện là console |
| Layout, component và `AppState` | `src/tts_cli/ui/` | Đã triển khai PySide6 desktop; `desktop.py` là launcher |
| Generate input | `generate_view.py`, `InputResolver` | Editor text rộng hoặc upload TXT/SRT/VTT |

Quy tắc cập nhật: khi parser, use case, port hoặc model thay đổi, phần tương
ứng trong tài liệu này phải được đối chiếu lại. Không lấy tên control, trạng
thái hoặc output giả định làm contract nếu chúng chưa tồn tại trong code.

## 1. Nguyên tắc nguồn duy nhất

UI phải gọi các use case và port hiện có, không tự gọi SDK, `ffmpeg`, hoặc thao tác output trực tiếp.

```text
UI adapter / web client
            -> application use cases
            -> core ports và models
            -> services / providers / adapters
```

Composition root hiện tại nằm ở `src/tts_cli/cli/commands.py`. Nếu thêm một UI
web, UI sẽ là một composition root/client mới và phải tái sử dụng cùng
`application`, `core`, `services`, `providers`, `adapters`.

UI hiện được triển khai thuần PySide6 trong cửa sổ desktop Windows. `tts-desktop`
là launcher chính; `tts-ui` là alias tương thích tới cùng application.
Dependency tương ứng là `.[ui]` và `.[desktop]`; CLI `tts` vẫn là entry point
độc lập.

## 2. Phạm vi tính năng có thật

| Khu vực UI | Command/use case hiện có | Kết quả |
| --- | --- | --- |
| Generate | `generate` -> `SynthesizeUseCase` | Project đánh số, MP3 tùy chọn, subtitle SRT/VTT/JSON tùy chọn |
| Batch | `batch` -> `BatchProcessUseCase` | Nhiều file TXT/SRT/VTT, progress và thống kê |
| Transcribe | `transcribe` -> `TranscribeUseCase` | Audio/video -> một file SRT |
| Voices | `voices` -> `VoiceListingUseCase` | Danh sách voice theo engine và bộ lọc |

Không thiết kế control cho tính năng chưa có contract, ví dụ chỉnh waveform, preview video, chỉnh cue thủ công, pause/resume hoặc export subtitle ngoài SRT ở workflow transcribe.

## 3. Layout tổng thể

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Header: Edge TTS CLI                         trạng thái tác vụ chính  │
├───────────────┬──────────────────────────────────────┬───────────────┤
│ Navigation    │ Main workspace                       │ Context panel │
│ Generate      │ Nội dung theo mode                   │ Cấu hình mode │
│ Batch         │                                      │               │
│ Transcribe    │                                      │               │
│ Voices        │                                      │               │
└───────────────┴──────────────────────────────────────┴───────────────┘
│ Bottom: engine | output context | tiến độ/kết quả | version | help   │
└──────────────────────────────────────────────────────────────────────┘
```

- Desktop: navigation bên trái, main workspace ở giữa, panel cấu hình bên phải.
- Tablet: navigation thành drawer; panel phải mở/đóng.
- Mobile: một cột; navigation và cấu hình dùng drawer hoặc bottom sheet.
- Chỉ hiển thị control liên quan đến mode đang chọn trong context panel.
- Header chỉ chứa nhận diện ứng dụng, mode hiện tại và trạng thái tác vụ chính.
- Bottom bar là vùng thông tin phụ cố định, gồm engine hiện tại, output context,
      tiến độ hoặc kết quả ngắn, version và liên kết trợ giúp nếu có.
- Không đặt form control, log dài hoặc thông báo lỗi chi tiết trong bottom bar;
      form cấu hình thuộc context panel, còn input/action/result thuộc main workspace.

Header hiển thị tên `Edge TTS CLI`, mode hiện tại và trạng thái tác vụ
(`Idle`, `Running`, `Succeeded`, `Failed`, `Cancelled`). Engine (`edge`, `google`,
hoặc `whisper`), output context và version `1.0.0` hiển thị ở bottom bar để
header không bị dồn thông tin. Không dùng “Clean Architecture Status” như
runtime status vì đây không phải trạng thái tác vụ.

`1.0.0` phải lấy từ metadata/package version hoặc một nguồn version được chọn
chung khi UI được triển khai; không hard-code một bản sao riêng trong UI.

## 4. Navigation và state chung

Navigation gồm bốn mode tương ứng với bốn subcommand:

1. **Generate**: tạo một project từ text hoặc file.
2. **Batch**: xử lý thư mục.
3. **Transcribe**: audio/video thành SRT bằng Whisper.
4. **Voices**: tra cứu voice của Edge hoặc Google.

State UI nên tách thành `AppState` gồm `active_mode`, `running_task`, `error_message`, `last_result`, `notifications`, cùng state riêng cho từng view. UI không bypass validation của `core.config.validate_args`.

## 5. Mode Generate

### Input

Cho phép chọn đúng một nguồn:

- **Text trực tiếp**: `-t/--text`.
- **File**: `-f/--file`, hỗ trợ UTF-8 `TXT`, `SRT`, `VTT` qua `InputResolver`.

Trong UI desktop, file được chọn bằng upload control, lưu tạm vào
`%TEMP%\\tts_cli_uploads`, sau đó truyền path tạm vào `InputResolver`. Không dùng
text input để yêu cầu người dùng tự gõ đường dẫn file.

UI báo lỗi nếu chọn cả hai; khi upload file, editor text được xóa để giữ đúng một
nguồn đầu vào. Editor text phải chiếm toàn bộ chiều rộng content và có chiều cao
tối thiểu ổn định để dùng như vùng soạn thảo chính. Với SRT/VTT, có thể hiển thị
preview text sau khi loại metadata và timestamp.

### Configuration

| Control | Giá trị hợp lệ / mặc định | Mapping |
| --- | --- | --- |
| Engine | `edge`, `google`; mặc định `edge` | `TTSConfig` / `TTSProviderFactory` |
| Voice | mặc định `vi-VN-HoaiMyNeural` | `TTSConfig.voice` |
| Rate | chuỗi như `+10%`, `-10%`, `+0%` | `TTSConfig.rate` |
| Pitch | chuỗi như `+2Hz`, `-2Hz`, `+0Hz` | `TTSConfig.pitch` |
| Volume | chuỗi như `-10%`, `+0%` | `TTSConfig.volume` |
| Subtitle mode | `phrase`, `sentence`, `word`; mặc định `phrase` | `subtitle_mode` |
| Max words | số nguyên; mặc định `8` | `max_words` |
| Output folder | mặc định `output` | `output_root`; CLI default nằm ở `cli.constants` |
| Output formats | `mp3`, `srt`, `vtt`, `json` | `OutputResolver` |
| Start number | mặc định `1` | `start` |
| Overwrite / Dry run | tắt mặc định | `overwrite` / `dry_run` |
| Retries / Timeout | `3` / `60.0` giây | `TTSConfig`; TTS defaults nằm ở `core.constants` |
| Proxy | tùy chọn, hiện dùng cho Edge | `TTSConfig.proxy` |

Google TTS không cung cấp word timing; UI phải cảnh báo subtitle timing có thể rỗng khi chọn Google.

### Progress và result

Progress của `SynthesizeUseCase`:

```text
0-70%   TTS
75%     subtitle
90%     output
100%    hoàn tất
```

Sau khi hoàn tất, hiển thị project number, số word cues, số subtitle cues,
duration và artifact thực tế. Các giá trị này lấy từ kết quả/use case hoặc
filesystem output, không tự tính lại ở UI. Audio player chỉ hiện khi chọn
`mp3` và file tồn tại; audio player là tiện ích UI, không phải capability hiện
có của application layer.

## 6. Mode Batch

| Control | Mapping |
| --- | --- |
| Source directory | positional `directory` |
| Recursive | `--recursive` |
| Output folder | `-o/--output`, mặc định `output` |
| Start number | `--start`, mặc định `1` |
| Skip existing | `--skip-existing` |
| Continue on error | `--continue-on-error` |
| Dry run | `--dry-run` |
| TTS/subtitle/output options | dùng chung với Generate |

Danh sách file chỉ gồm `.txt`, `.srt`, `.vtt`, được `BatchFileService` sắp xếp trước khi xử lý. UI nên hiển thị preview và project number dự kiến.

Hiển thị `current/total`, file hiện tại, `Success`, `Skipped`, `Failed` và log lỗi theo file. Khi tắt `continue_on_error`, lỗi đầu tiên dừng batch; khi bật, batch tiếp tục. `KeyboardInterrupt` và cancellation không được coi là lỗi file thông thường. Progress phải finish khi batch dừng bất thường.

## 7. Mode Transcribe

| Control | Giá trị |
| --- | --- |
| Source media | file audio hoặc video |
| Engine | chỉ `whisper` |
| Output | một file SRT, mặc định `subtitle.srt` |
| Model size | `tiny`, `base`, `small`, `medium`, `large-v3`; mặc định `base` |
| Language | tùy chọn, mặc định tự nhận diện |
| Device | `auto`, `cpu`, `cuda`; mặc định `auto` |

UI kiểm tra source là audio/video trước khi chạy. Whisper local cần extra `.[whisper]`; media provider cần cả `ffmpeg` và `ffprobe` trong PATH.

Kết quả hiển thị số cue, language nếu provider trả về, preview subtitle và
đường dẫn SRT. `TranscribeUseCase.execute()` trả `TranscriptResult`; UI có thể
dùng result này để hiển thị metadata, nhưng CLI hiện tại chỉ in đường dẫn sau
khi use case hoàn tất. Không hiển thị MP3 output vì `TranscribeUseCase` chỉ ghi
SRT.

## 8. Mode Voices

| Control | Mapping |
| --- | --- |
| Engine | `edge` hoặc `google` |
| Language | khớp locale hoặc voice name |
| Gender | `Male` hoặc `Female` |
| Search | voice name, locale, friendly name |

Bảng dùng các field `ShortName`, `Locale`, `Gender`. Có thể giữ
`FriendlyName` làm metadata nếu provider trả về. Empty state là “Không tìm
thấy voice.”. Khi chọn voice, UI có thể chuyển sang Generate và điền
`TTSConfig.voice`. `VoiceListingUseCase` hiện in bảng bằng `print`; UI không
nên gọi use case console này trực tiếp nếu cần dữ liệu có cấu trúc. Cần thêm
application result/presenter hoặc một port trình bày riêng trước khi triển
khai UI web.

## 9. Error, loading và cancellation

- Disable control gây chạy trùng khi tác vụ đang `Running`.
- Validation hiển thị tại control; lỗi provider/filesystem hiển thị ở vùng kết quả chung.
- Với `RetryExhaustedError`, hiển thị số attempt và nguyên nhân gốc (`cause`), không chỉ message generic. Exception này vẫn tương thích với `RuntimeError`.
- Timeout/connection error dùng cùng hint semantics với `__main__.py`.
- Cleanup artifact do application/output layer xử lý; UI chỉ refresh trạng thái filesystem.
- `Ctrl+C` là semantics CLI. UI web cần application cancellation contract riêng, không tự hủy task tùy ý.

## 10. Accessibility và interaction

- Mọi input có label và trạng thái lỗi đọc được.
- Tab order: input -> configuration -> action -> result.
- Nút dùng verb rõ: `Generate`, `Start batch`, `Transcribe`, `Load voices`.
- Hiển thị đơn vị cho rate, pitch, volume, timeout và max words.
- Confirmation chỉ dùng trước overwrite; dry-run không tạo artifact.
- Không dựa chỉ vào màu để phân biệt trạng thái.

## 11. Cấu trúc UI đã triển khai

```text
ui/
├── app.py                 # PySide6 main window và UI composition root
├── desktop.py             # Windows desktop entry point
├── state.py               # session state
└── state.py               # application/session state
```

Các view gọi `SynthesizeUseCase`, `BatchProcessUseCase`, `TranscribeUseCase` và
`VoiceCatalogService` qua UI composition root. Các provider và adapter được tạo
ở các boundary hiện có; view không gọi trực tiếp SDK hoặc `subprocess`.

Layout runtime trong `app.py` được tổ chức thành:

```text
header
      navigation | main workspace | context panel
footer / bottom bar
```

`main workspace` chứa input, action, progress, lỗi và kết quả. `context_panel`
chứa configuration theo mode: TTS/output cho Generate và Batch, model/device/
language/output cho Transcribe, engine/language/gender/search cho Voices. Các
view dùng dictionary trong `AppState` để hai vùng bind cùng một state, không tạo
bản sao cấu hình riêng.

### Chế độ chạy

| Entry point | Hiển thị | Dependency |
| --- | --- | --- |
| `tts-ui` | Cửa sổ desktop PySide6 | `.[ui]` |
| `tts-desktop` | Cửa sổ desktop PySide6 | `.[desktop]` |

`app.main()` là điểm dùng chung. Desktop launcher không có business logic riêng.

### Trạng thái triển khai

- Đã có: header, navigation, main workspace, context panel, bottom bar, trạng thái task, lỗi,
      form Generate/Batch/Transcribe/Voices và responsive layout cơ bản bằng
      Tailwind classes của NiceGUI.
- Đã có: `AppState` với `Idle`, `Running`, `Succeeded`, `Failed` và state kết
      quả gần nhất.
- Chưa có: upload file trực tiếp, preview audio, bảng voice có cấu trúc trong
      application layer, cancellation web và progress streaming chi tiết.
- Các mục chưa có vẫn cần application contract riêng trước khi thêm control UI.

## 12. Audit kết luận và Definition of Done

### Kết luận audit

- Bốn mode trong blueprint tương ứng với bốn command/use case đang có.
- Generate, batch, output formats, retry, cleanup, progress và transcription
      đã có contract đủ rõ để thiết kế UI adapter.
- Layout header/main/context/bottom là đề xuất UI, chưa phải runtime layout.
- Voice listing hiện còn phụ thuộc console presentation; đây là blocker kỹ
      thuật duy nhất trước khi tái sử dụng trực tiếp cho UI web có dữ liệu bảng.
- Không được mô tả pause/resume, chỉnh cue, waveform, preview video hoặc
      cancellation web như tính năng đã có.

### Definition of Done

- [x] Thêm UI framework dependency và entry point riêng vào `pyproject.toml`.
- [x] UI gọi use case qua composition root, không tạo provider trong view.
- [x] Bốn mode map đúng parser contract hiện tại.
- [ ] Có loading, success, validation error, provider error, cancellation và empty state.
- [x] Artifact list lấy từ application/output layer, không hard-code khác contract.
- [ ] Test UI giữ offline behavior và mock provider/network như test hiện tại.
- [x] README cập nhật lệnh chạy desktop UI sau khi UI thật sự được triển khai.