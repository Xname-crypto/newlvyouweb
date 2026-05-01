@echo off
chcp 65001 > nul
echo 正在请求微调模型...
curl -s -X POST https://open.bigmodel.cn/api/paas/v4/chat/completions ^
-H "Authorization: Bearer 06d9bc9bf85e41a78d3bc36ce9e46b4e.mVj71EDA6f6q53C4" ^
-H "Content-Type: application/json" ^
-d "{\"model\": \"glm-4-flash:881617285:travel:xpe5vwbl\", \"messages\": [{\"role\": \"user\", \"content\": \"请介绍一下上海的东方明珠。\"}]}"
