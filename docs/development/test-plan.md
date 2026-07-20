# テスト計画

## 方針

Pythonコードはpytest、Ruff、mypyで確認する。Docker、ネットワーク、Lightsailは単体テストだけでは十分に確認できないため、統合テストと受け入れテストで実動作を確認する。

テストでは実IP、実パスワード、実攻撃ログをfixtureに使わない。必要なログは合成データを使用する。

## 単体テスト

対象:

- Cowrie JSON Linesの読み込み
- 空行の処理
- 不正JSON行のスキップ
- 必須項目が欠けたイベントの処理
- 未知イベントIDの処理
- ユーザー名集計
- パスワード集計
- 送信元IP集計
- コマンド集計
- セッション別コマンド集計
- コマンド分類
- IPv4匿名化
- IPv6匿名化
- CSV出力
- 空ログの処理
- 大きなログを逐次処理できること

実行コマンド:

```powershell
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python -m mypy src
```

正常な結果:

- pytestが成功する。
- Ruffが成功する。
- mypyが成功する。

## ローカル統合テスト

目的:

ローカル環境でCowrie観測、ログ永続化、ログ分析、外向き通信制限を一連の流れとして確認する。

実行コマンド:

```powershell
docker compose config
docker compose up -d
docker compose ps
Test-NetConnection 127.0.0.1 -Port 2222
.\.venv\Scripts\python scripts\exercise_cowrie_ssh.py --host 127.0.0.1 --port 2222 --username root --password admin --command "uname -a"
.\.venv\Scripts\python -m cowrie_observer.cli analyze --input logs\cowrie\cowrie.json --output data\public\summary.csv
Get-Content data\public\summary.csv
.\scripts\verify_egress.ps1
docker compose down
```

正常な結果:

- `cowrie` が起動する。
- `cowrie-ssh-proxy` は起動しない。
- `127.0.0.1:2222` に接続できる。
- SSHログイン試行とコマンド入力がCowrieログに記録される。
- CSVが生成される。
- CSVにパスワードが含まれない。
- CSVのIPが匿名化される。
- Cowrie本体から外部通信できない。
- 停止後も `logs/cowrie/` のログが残る。

## Lightsail受け入れテスト

目的:

GitHubからcloneしたリポジトリを使い、Lightsail上で安全にCowrieを公開できることを確認する。

前提:

- Lightsailインスタンスが作成済みである。
- 静的IPがアタッチ済みである。
- 管理用OpenSSHが22番以外へ移動済みである。
- 管理用OpenSSHは管理者IP/32からのみ接続できる。
- LightsailファイアウォールでTCP 22番がCowrie用に許可されている。
- IPv6側に意図しない開放がない。
- Docker EngineとDocker Compose pluginが導入済みである。

サーバー上の確認:

```bash
git clone <PUBLIC_REPOSITORY_URL>
cd Cowrie-Honeypot
cp .env.lightsail.example .env
sudo docker compose config
sudo docker compose up -d
sudo docker compose ps
```

正常な結果:

- `cowrie` が起動している。
- Cowrieコンテナ自身が `0.0.0.0:22->2222/tcp` を公開している。
- `cowrie-ssh-proxy` は起動していない。
- Dockerネットワークに固定サブネットが設定されている。
- Cowrieコンテナの外向き通信を遮断するホスト側firewallが設定されている。

外部端末からの確認:

```bash
ssh -p 22 root@<LIGHTSAIL_STATIC_IP>
ssh -p 22222 ubuntu@<LIGHTSAIL_STATIC_IP>
```

正常な結果:

- 22番の接続先はCowrieである。
- 管理用ポートは管理者IPからのみ接続できる。
- 管理者IP以外から管理用ポートへ接続できない。

サーバー上のログ確認:

```bash
sudo docker compose logs --tail=50 cowrie
ls -l logs/cowrie
```

正常な結果:

- 外部端末からの接続がCowrieログへ記録されている。
- Cowrie JSONログの `src_ip` に外部端末の実送信元IPが記録されている。
- `src_ip` がDocker内部IPやproxyコンテナIPだけになっていない。
- コンテナ再作成後もログが残る。
- 偽シェル内で入力した `whoami`、`uname -a`、`ls` などのコマンドがCowrieログへ記録される。
- `curl http://example.com` のような外向き通信は失敗し、Cowrieログに通信ブロックが記録される。

失敗条件:

- Cowrieログ上の `src_ip` がDocker内部IPだけになる。
- 偽シェル内の `curl http://example.com` が外部へ成功する。
- 管理用OpenSSHがTCP 22番で待ち受けている。
- TCP 22222などの管理用ポートが任意のIPv4へ公開されている。

外向き通信制限:

```bash
./scripts/verify_egress.sh
```

正常な結果:

```text
OK: outbound connection was blocked.
```

確認対象は `cowrie` 本体である。

## 公開前チェック

公開またはpush前に確認する。

```powershell
git status --short
rg -n "BEGIN|PRIVATE|SECRET|TOKEN|AWS_ACCESS|AKIA|password=|hikar|AppData" README.md AGENTS.md docs src tests scripts .env.example .env.lightsail.example compose.yaml pyproject.toml
```

正常な結果:

- 秘密情報や環境固有情報がヒットしない。
- 生ログや生成CSVがGit差分に含まれない。
