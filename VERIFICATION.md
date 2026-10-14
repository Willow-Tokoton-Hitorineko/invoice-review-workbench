# Local verification

Date: 2026-10-14 (Asia/Shanghai).
Runtime: Python 3.12.14 on Windows.

- `python -m unittest discover -s tests -v`: 9 tests passed, zero failures.
- `python workbench.py`: exit code 0; output parsed as JSON.
- Inputs are synthetic. No remote database or paid API was called.

This verifies the public demonstration only, not the original private project or production performance. GitHub Actions status is recorded separately after publishing.


## 交互升级验证 · 2026-10-14

真实浏览器以三条合成票据验证：首次未确认导出禁用；校验显示缺失字段和无效金额原因；逐行补齐、修正事实、确认后全部通过；编辑金额撤销该行确认并重新禁用导出；重新确认与校验后 CSV 导出成功。已有 9 项后端测试通过。页面截图仅含合成测试输入，不含公司或个人票据。
