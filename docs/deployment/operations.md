# 運用手順

## 対象範囲

この文書は、ローカル検証、AWS Lightsailへの手動デプロイ、停止、復旧、監視の手順を定義する。

CodexはAWSリソース作成、Lightsail設定変更、SSH設定変更、ファイアウォール変更を自動実行しない。AWS上の操作は人間が内容を確認して手動で行う。

まっさらなLightsailへSSHログインした状態から順に作業する場合は、先に `docs/deployment/lightsail-setup.md` を参照する。

## 設計上の選択

- 確定: ローカル環境ではCowrieをインターネットへ公開しない。
- 確定: LightsailではTCP 22番をCowrie観測用SSHとして使う。
- 確定: 管理用OpenSSHはTCP 22番以外へ移動し、管理者IPからのみ許可する。
- 確定: LightsailへのデプロイはGitHubからcloneしたリポジトリを使う。
- 確定: 生ログ、`.env`、秘密鍵、AWS認証情報はGitへコミットしない。
- 確定: LightsailではCowrieコンテナ自身をTCP 22番へ直接公開し、実送信元IPをログへ残す。
- 確定: `cowrie-ssh-proxy` は実送信元IPを失うため、Lightsail運用では使わない。
- 暫定: LightsailのOSはUbuntu LTSを想定する。
- 暫定: 管理用OpenSSHの待ち受けポートは `22222` を例とする。
- 暫定: Cowrieコンテナの外向き通信制限はホスト側firewallで実装する。
- 暫定: Dockerネットワークは固定サブネット化する。
- 未決: Lightsailのインスタンスサイズ、リージョン、ディスク容量、ログ保存期間。
- 未決: 長期運用時のログバックアップ先。
- 未決: 監視通知先と通知方法。

## ローカル運用

### 起動

```powershell
docker compose config
docker compose up -d
docker compose ps
```

正常な結果:

- `cowrie` が起動している。
- `cowrie` だけが `127.0.0.1:2222` を公開している。

### 疎通確認

```powershell
Test-NetConnection 127.0.0.1 -Port 2222
.\.venv\Scripts\python scripts\exercise_cowrie_ssh.py --host 127.0.0.1 --port 2222 --username root --password admin --command "uname -a"
```

正常な結果:

- `TcpTestSucceeded : True` が表示される。
- Cowrieのシェル応答が表示される。
- `logs/cowrie/cowrie.json` に接続、ログイン、コマンド入力イベントが記録される。

### 外向き通信制限確認

```powershell
.\scripts\verify_egress.ps1
```

正常な結果:

```text
OK: outbound connection was blocked.
```

### 停止

```powershell
docker compose down
```

## Lightsailデプロイ前チェック

AWS上で作業する前に、ローカルで次を確認する。

```powershell
git status --short
docker compose config
docker compose --env-file .env.lightsail.example config
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python -m mypy src
```

確認ポイント:

- コミット漏れがない。
- 生ログ、`.env`、秘密鍵、実IP、AWS認証情報が差分に含まれていない。
- Lightsail用環境変数では `cowrie` が `0.0.0.0:22` を公開する。
- `cowrie-ssh-proxy` が構成に残っていない。
- Dockerネットワークの固定サブネットとホスト側firewallによる外向き通信制限の手順が確認できる。

## Lightsailインスタンス作成

### 推奨初期構成

- プラットフォーム: Linux/Unix
- OS: Ubuntu LTS
- ネットワーク: IPv4を使用
- IPv6: 使わない場合は無効化またはファイアウォールで閉じる
- 静的IP: 作成してインスタンスへアタッチする

Lightsailでは、静的IPを使わずに停止または再起動するとパブリックIPが変わる可能性がある。観測先を固定するため、静的IPを使う。

## Lightsailファイアウォール

LightsailにはIPv4用とIPv6用のファイアウォールがある。IPv6を有効にする場合は、IPv4とは別にIPv6側も確認する。

初期ルール例:

| 用途 | プロトコル | ポート | 接続元 |
| --- | --- | --- | --- |
| Cowrie観測用SSH | TCP | 22 | 任意のIPv4 |
| 管理用OpenSSH | TCP | 22222 | 管理者の固定IP/32 |
| HTTP/HTTPS | TCP | 80/443 | 開けない |
| Telnet | TCP | 23 | 開けない |
| その他 | 任意 | 任意 | 開けない |

重要:

- 管理用OpenSSHを22番のまま外部公開しない。
- 管理用OpenSSHの接続元を `0.0.0.0/0` にしない。
- IPv6を使わないなら、IPv6側に意図しない開放がないことを確認する。

## 管理用OpenSSHの移動

Lightsailへ初回接続した直後は、管理用OpenSSHが22番で待ち受けている可能性がある。Cowrieへ22番を渡す前に、管理用OpenSSHを別ポートへ移動する。

例では `22222` を使う。

手順:

1. LightsailファイアウォールでTCP `22222` を管理者IP/32に限定して許可する。
2. 既存のSSHセッションは閉じずに残す。
3. サーバー上でOpenSSHの設定を変更し、待ち受けポートに `22222` を追加する。
4. OpenSSHを再読み込みまたは再起動する。
5. 別ターミナルから `22222` で接続できることを確認する。
6. `22222` で接続できるまで、既存のSSHセッションを閉じない。
7. 22番で管理用OpenSSHが待ち受けていないことを確認する。

確認例:

```bash
ssh -i /path/to/key.pem -p 22222 ubuntu@<LIGHTSAIL_STATIC_IP>
sudo ss -ltnp | grep sshd
```

Ubuntuのユーザー名は通常 `ubuntu` である。Lightsailのイメージにより異なる場合は、Lightsailの接続画面で確認する。

## Docker導入

Ubuntu上ではDocker EngineとDocker Compose pluginを導入する。手順はDocker公式ドキュメントのUbuntu向けapt repository方式に従う。

確認コマンド:

```bash
sudo systemctl status docker
sudo docker version
sudo docker compose version
```

正常な結果:

- Docker daemonが起動している。
- `docker compose version` が表示される。

## GitHubからデプロイ

### clone

```bash
git clone <PUBLIC_REPOSITORY_URL>
cd Cowrie-Honeypot
```

### `.env` 作成

```bash
cp .env.lightsail.example .env
```

Lightsailでは必要に応じて次を確認する。

```dotenv
COWRIE_IMAGE=cowrie/cowrie:latest
COWRIE_SSH_BIND_ADDRESS=0.0.0.0
COWRIE_SSH_PORT=22
TZ=UTC
```

`.env` はGitへコミットしない。

### 起動

```bash
sudo docker compose config
sudo docker compose up -d
sudo docker compose ps
```

正常な結果:

- `cowrie` が起動している。
- `cowrie` が `0.0.0.0:22->2222/tcp` を公開している。
- `cowrie-ssh-proxy` は起動していない。
- OpenSSHは22番ではなく管理用ポートで待ち受けている。

## Lightsail受け入れ確認

外部端末から確認する。

```bash
ssh -p 22 root@<LIGHTSAIL_STATIC_IP>
```

正常な結果:

- 接続先は管理用OpenSSHではなくCowrieである。
- Cowrie JSONログの `src_ip` に外部端末の実送信元IPが記録される。
- `src_ip` がDocker内部IPやproxyコンテナIPだけになっていない。
- ログイン試行や入力コマンドがCowrieログへ記録される。

サーバー上で確認する。

```bash
sudo docker compose logs --tail=50 cowrie
ls -l logs/cowrie
sudo docker compose exec -T cowrie /cowrie/cowrie-env/bin/python3 -c "print('ok')"
```

外向き通信制限を確認する。

```bash
sudo ./scripts/verify_egress.sh
```

確認対象は `cowrie` 本体である。

## ログ分析

Ubuntuで `ensurepip is not available` と表示される場合は、先に `.venv` 作成用パッケージを入れる。

```bash
sudo apt install -y python3-venv
```

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -e .[dev]
ls -la logs/cowrie
./.venv/bin/python -m cowrie_observer.cli analyze --input logs/cowrie/cowrie.json --output data/public/summary.csv
```

公開用CSVは匿名化済みである。ただし、生成物はGitへコミットしない。

`logs/cowrie/cowrie.json` が存在しない場合は、`ls -la logs/cowrie` と `sudo docker compose logs --tail=100 cowrie` でログ出力状況を確認する。必要に応じて外部端末からCowrieへ接続し、ログイン試行やコマンド入力を発生させる。

## 停止

通常停止:

```bash
sudo docker compose down
```

緊急停止:

```bash
sudo docker stop cowrie-observer
```

Lightsail側で即時遮断する場合:

- LightsailファイアウォールからTCP 22番を閉じる。
- 必要に応じてインスタンスを停止する。

## 復旧

復旧時の基本手順:

1. 管理用OpenSSHへ接続できることを確認する。
2. `git status --short` でサーバー上の変更を確認する。
3. 必要ならログを退避する。
4. `sudo docker compose down` を実行する。
5. `sudo docker compose up -d` を実行する。
6. Cowrieへの22番接続、ログ記録、外向き通信制限を再確認する。

## 監視

初期運用で確認する項目:

- Lightsailの料金アラート
- ディスク使用率
- `logs/cowrie/` の容量
- Cowrieコンテナの起動状態
- Cowrieコンテナの起動状態
- TCP 22番がCowrieへ到達すること
- Cowrieログの `src_ip` に実送信元IPが記録されること
- 管理用OpenSSHが管理者IPからのみ接続できること
- IPv6側に意図しない開放がないこと
- Cowrie本体から外部通信できないこと

## 参考

- Amazon Lightsail: SSH接続とSSHキー
- Amazon Lightsail: ファイアウォールとポート
- Amazon Lightsail: 静的IP
- Docker Docs: Install Docker Engine on Ubuntu
