# 示例输出说明

本目录不保存运行期产物。

当前线上主路径会在请求内生成并直接返回 `.docx` 文件，不再把 `outputs/jobs/{job_id}/` 作为主状态或主产物目录。

如需本地调试落盘，可设置 `SCNU_DEBUG_PERSIST_ARTIFACTS=1`，调试产物会进入 `outputs/debug/`。本目录仅用于后续放置截图、样例 manifest 或说明文档。
