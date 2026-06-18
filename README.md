# lenlion-project

Lenlion 工作区 monorepo。当前包含一个独立子项目：

```
lenlion-project/
├── .github/          # CI / Issue 模板（working-directory: lenlion_agent）
└── lenlion_agent/    # Lenlion Agent 独立项目
```

## 快速开始

```bash
cd lenlion_agent
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[cli,pty,mcp,cron]"
lenlion setup
lenlion
```

完整文档见 [lenlion_agent/README.md](./lenlion_agent/README.md)。
