# Cowrie-Honeypot

AWS上でCowrieを安全に運用し、SSHハニーポットのログを収集・正規化・集計するための学習用プロジェクトです。

このリポジトリは公開リポジトリとして扱います。秘密情報、実IPを含む生ログ、秘密鍵、マルウェア検体、ダウンロード成果物、個人メモはコミットしないでください。

## ドキュメント

- [プロジェクト概要](docs/project-brief.md)
- [要件定義](docs/requirements.md)
- [アーキテクチャ](docs/architecture.md)
- [セキュリティ](docs/security.md)
- [テスト計画](docs/test-plan.md)
- [開発計画](docs/development-plan.md)
- [Codex作業手順](docs/codex-workflow.md)
- [運用手順](docs/operations.md)

## 前提

- Python 3.11以上
- Docker Desktop
- PowerShell

Pythonコマンドは必ずプロジェクト直下の仮想環境 `.venv` で実行します。システムPythonへ直接ライブラリを入れないでください。

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e .[dev]
```

## ローカルCowrieの起動

Docker Desktopを起動してから、設定の確認と起動を行います。

```powershell
docker compose config
docker compose up -d
docker compose ps
```

Cowrieはローカルホストのみに公開します。

```powershell
Test-NetConnection 127.0.0.1 -Port 2222
```

`TcpTestSucceeded : True` が表示されれば、ホストPCからCowrieへ接続できます。

ローカル構成では、Cowrie本体を内部ネットワークに置き、`cowrie-ssh-proxy` だけが `127.0.0.1:2222` を受け付けます。これにより、ホストPCからのSSH確認とCowrie本体の外向き通信制限を両立します。

## ローカル動作確認

テスト用SSH接続を行い、Cowrieにコマンド入力イベントを記録させます。

```powershell
.\.venv\Scripts\python scripts\exercise_cowrie_ssh.py --host 127.0.0.1 --port 2222 --username root --password admin --command "uname -a"
```

ログが出ていることを確認します。

```powershell
Get-ChildItem logs\cowrie
```

## ログ集計

CowrieのJSONログから公開用CSVを生成します。

```powershell
.\.venv\Scripts\python -m cowrie_observer.cli analyze --input logs\cowrie\cowrie.json --output data\public\summary.csv
Get-Content data\public\summary.csv
```

公開用CSVでは送信元IPを匿名化し、パスワードは出力しません。ただし生成物は検証用ファイルなので、`data/public/` 配下はGit管理しません。

## 外向き通信制限の確認

ハニーポットから外部へ通信できないことを確認します。

```powershell
.\scripts\verify_egress.ps1
```

`OK: outbound connection was blocked.` が正常です。`NG: outbound connection succeeded.` が表示された場合は、Dockerネットワークまたはホスト側ファイアウォールの設計を見直してください。

外向き通信確認の対象はCowrie本体です。`cowrie-ssh-proxy` はローカルホストからCowrieへ接続を中継するための補助コンテナです。

## 停止

確認が終わったら、Cowrieを停止します。

```powershell
docker compose down
```

## Git管理しないもの

次のファイルやディレクトリは公開リポジトリに含めません。

- `.env`
- `.venv/`
- `logs/`
- `data/raw/`
- `data/normalized/`
- `data/public/`
- `data/downloads/`
- `*.pem`
- `*.key`
