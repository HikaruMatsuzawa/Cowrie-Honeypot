# Cowrie-Honeypot

AWS Lightsail上でCowrieを安全に運用し、SSHハニーポットのログを収集・正規化・集計するための学習用プロジェクトです。

このリポジトリは公開リポジトリとして扱います。秘密情報、実IPを含む生ログ、秘密鍵、マルウェア検体、ダウンロード成果物、個人メモはコミットしないでください。

## ドキュメント

まず [ドキュメント一覧](docs/README.md) を見ると、開発用とデプロイ・運用用の文書を分けて確認できます。

開発するときに見る文書:

- [プロジェクト概要](docs/development/project-brief.md)
- [要件定義](docs/development/requirements.md)
- [アーキテクチャ](docs/development/architecture.md)
- [セキュリティ](docs/development/security.md)
- [テスト計画](docs/development/test-plan.md)
- [開発計画](docs/development/development-plan.md)
- [Codex作業手順](docs/development/codex-workflow.md)

デプロイ・運用するときに見る文書:

- [運用手順](docs/deployment/operations.md)
- [Lightsail初回セットアップ手順](docs/deployment/lightsail-setup.md)

## 構成の考え方

- ローカルではCowrieを外部公開せず、`127.0.0.1:2222` だけで確認します。
- Lightsailでは管理用OpenSSHを22番以外へ移動し、インターネットからのTCP 22番をCowrieへ割り当てます。
- Cowrie本体はDocker内部ネットワークに配置し、SSHプロキシコンテナだけがホスト側ポートを受けます。
- Cowrie本体から外部への通信は遮断します。
- 生ログはローカルまたはサーバー上に残しますが、Gitには載せません。

## ローカル開発の前提

- Python 3.11以上
- Docker Desktop
- PowerShell

Pythonコマンドは必ずプロジェクト直下の仮想環境 `.venv` で実行します。

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e .[dev]
```

## ローカルCowrieの起動

Docker Desktopを起動してから、設定確認と起動を行います。

```powershell
docker compose config
docker compose up -d
docker compose ps
```

Cowrieはローカルホストのみに公開されます。

```powershell
Test-NetConnection 127.0.0.1 -Port 2222
```

`TcpTestSucceeded : True` が表示されれば正常です。

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

Cowrie本体から外部へ通信できないことを確認します。

```powershell
.\scripts\verify_egress.ps1
```

`OK: outbound connection was blocked.` が正常です。

## ローカル停止

確認が終わったら、Cowrieを停止します。

```powershell
docker compose down
```

## Lightsailへデプロイする場合

まっさらなLightsailへSSHログインした直後から進める場合は、まず [Lightsail初回セットアップ手順](docs/deployment/lightsail-setup.md) を確認してください。運用全体の整理は [運用手順](docs/deployment/operations.md) にあります。

概要は次の流れです。

1. LightsailでUbuntuインスタンスを作成する。
2. 静的IPを作成してインスタンスへアタッチする。
3. Lightsailファイアウォールで管理用SSHとCowrie用22番のルールを分ける。
4. 管理用OpenSSHを22番以外へ移動し、管理者IPからのみ接続できるようにする。
5. GitHubからこのリポジトリをcloneする。
6. Docker EngineとCompose pluginをインストールする。
7. `.env.lightsail.example` を参考に `.env` を作成する。
8. `compose.yaml` を使ってCowrieを起動する。
9. 22番がCowrieへ到達し、管理用OpenSSHが22番で待ち受けていないことを確認する。
10. 外向き通信制限、ログ永続化、停止・復旧手順を確認する。

Lightsail上の起動コマンドは次の形式です。

```bash
cp .env.lightsail.example .env
sudo docker compose config
sudo docker compose up -d
./scripts/verify_egress.sh
```

この操作はインターネットからTCP 22番へ到達できる構成を作るため、必ず [セキュリティ](docs/development/security.md) と [運用手順](docs/deployment/operations.md) を確認してから実行してください。

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
