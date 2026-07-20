# Lightsail初回セットアップ手順

## この手順書の目的

この文書は、まっさらなAmazon LightsailのUbuntuインスタンスへSSHログインできた状態から、Cowrieハニーポットを安全に公開するまでの一本道の手順をまとめたものである。

この手順では、次の状態を目標にする。

- 管理用OpenSSHはTCP 22番で公開しない。
- 管理用OpenSSHは管理者IPからのみ接続できる。
- インターネットからTCP 22番へ接続するとCowrieへ到達する。
- Cowrie本体はDocker内部ネットワークに置き、外向き通信できない。
- 生ログ、秘密鍵、`.env`、実IPをGitへ載せない。

## 全体の流れ

1. Lightsail画面で静的IPを設定する。
2. Lightsail画面で管理用SSHポートを一時的に追加する。
3. サーバーへSSHログインする。
4. サーバー側のOpenSSHを22番以外へ移す。
5. 新しい管理用SSHポートでログインできることを確認する。
6. Lightsail画面でファイアウォールを最終形にする。
7. サーバーへDocker EngineとDocker Compose pluginを入れる。
8. GitHubからリポジトリをcloneする。
9. Lightsail用 `.env` を作成する。
10. Cowrieを起動する。
11. Cowrie到達、ログ保存、外向き通信制限を確認する。
12. 停止・復旧・監視方法を確認する。

## 前提

- LightsailでUbuntuインスタンスを作成済みである。
- LightsailのブラウザSSH、またはローカルPCからのSSHでインスタンスへログインできる。
- GitHub上にこのリポジトリがpush済みである。
- 管理者のグローバルIPアドレスを確認できる。

この手順では、例として次の値を使う。

| 項目 | 例 |
| --- | --- |
| 管理用Linuxユーザー | `ubuntu` |
| 管理用OpenSSHポート | `22222` |
| Cowrie公開ポート | `22` |
| リポジトリURL | `<PUBLIC_REPOSITORY_URL>` |
| Lightsail静的IP | `<LIGHTSAIL_STATIC_IP>` |
| 管理者IP | `<YOUR_GLOBAL_IP>/32` |

実際のIPアドレスや秘密鍵パスは、README、docs、Issue、コミットに貼らない。

## 1. Lightsail画面で静的IPを設定する

Lightsailの動的パブリックIPは、インスタンスの停止や再起動で変わる可能性がある。観測先を固定するため、先に静的IPを作成してインスタンスへアタッチする。

Lightsail画面で行うこと:

1. Lightsailコンソールを開く。
2. `Networking` を開く。
3. `Create static IP` を選ぶ。
4. 対象インスタンスと同じリージョンを選ぶ。
5. 対象インスタンスへ静的IPをアタッチする。
6. 静的IPを控える。

確認ポイント:

- 静的IPが対象インスタンスへアタッチされている。
- 以降の接続先は動的IPではなく静的IPを使う。

## 2. Lightsail画面で初期ファイアウォールを設定する

最初は管理用OpenSSHがTCP 22番で待ち受けている可能性がある。いきなり22番をCowrieへ渡すと、サーバーへ入れなくなる危険がある。

まず、管理用OpenSSHの移動先としてTCP `22222` を追加する。

Lightsail画面で行うこと:

| 用途 | プロトコル | ポート | 接続元 |
| --- | --- | --- | --- |
| 初期管理用SSH | TCP | 22 | 管理者IP/32 |
| 新管理用SSH | TCP | 22222 | 管理者IP/32 |

注意:

- 管理用SSHを `0.0.0.0/0` へ開けない。
- IPv6を使わないなら、IPv6側のファイアウォールに意図しない許可がないことを確認する。
- LightsailのIPv4ファイアウォールとIPv6ファイアウォールは独立しているため、両方を見る。

## 3. サーバーへSSHログインする

ローカルPCから接続する例:

```bash
ssh -i /path/to/key.pem -p 22 ubuntu@<LIGHTSAIL_STATIC_IP>
```

LightsailのブラウザSSHを使ってもよい。

確認ポイント:

- `ubuntu` ユーザーでログインできる。
- まだこの時点では既存のSSHセッションを閉じない。

## 4. 管理用OpenSSHを22番以外へ移す

UbuntuのOpenSSH設定は環境により場所が異なることがある。まず現在の待ち受け状態を確認する。

```bash
sudo ss -ltnp | grep sshd
```

OpenSSHの設定ファイルを確認する。

```bash
sudo sshd -T | grep '^port '
```

`/etc/ssh/sshd_config` または `/etc/ssh/sshd_config.d/` 配下の設定で、管理用ポート `22222` を有効にする。

例:

```bash
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
sudo sudoedit /etc/ssh/sshd_config
```

設定例:

```text
Port 22222
PasswordAuthentication no
PermitRootLogin no
```

設定構文を確認する。

```bash
sudo sshd -t
```

OpenSSHを再読み込みする。

```bash
sudo systemctl reload ssh
```

もし `ssh` サービス名で失敗する場合は、次を確認する。

```bash
systemctl list-units --type=service | grep ssh
```

重要:

- 新しい接続が成功するまで、現在のSSHセッションを閉じない。
- `sshd -t` が失敗した状態で再起動しない。
- 22番を閉じる前に、必ず22222番でログインできることを確認する。

## 5. 新しい管理用SSHポートで接続確認する

別ターミナルから確認する。

```bash
ssh -i /path/to/key.pem -p 22222 ubuntu@<LIGHTSAIL_STATIC_IP>
```

正常な結果:

- 22222番でログインできる。
- 既存の22番接続を閉じても、22222番で再ログインできる。

サーバー上で待ち受けを確認する。

```bash
sudo ss -ltnp | grep sshd
```

確認ポイント:

- OpenSSHが22222番で待ち受けている。
- 最終的にはOpenSSHが22番で待ち受けていない状態にする。

## 6. Lightsail画面でファイアウォールを最終形にする

OpenSSHの新ポート接続が確認できたら、Lightsailファイアウォールを最終形へ変更する。

IPv4ファイアウォール:

| 用途 | プロトコル | ポート | 接続元 |
| --- | --- | --- | --- |
| Cowrie観測用SSH | TCP | 22 | 任意のIPv4 |
| 管理用OpenSSH | TCP | 22222 | 管理者IP/32 |

閉じるもの:

- TCP 23
- TCP 80
- TCP 443
- 不要な全ポート

IPv6ファイアウォール:

- IPv6を使わない場合は、SSHや不要ポートを開けない。
- IPv6を使う場合は、IPv4と同じ考え方で明示的に制限する。

確認ポイント:

- 管理用OpenSSHは管理者IPからのみ接続できる。
- 管理用OpenSSHを `0.0.0.0/0` へ開けていない。
- TCP 22番はCowrie用として開ける。
- TCP 23番は開けない。

## 7. サーバーの基本パッケージを更新する

サーバーにログインした状態で実行する。

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y ca-certificates curl git
```

確認ポイント:

- エラーなく完了する。
- 再起動が必要と表示された場合は、管理用SSHで再接続できることを確認してから再起動する。

## 8. Docker EngineとCompose pluginをインストールする

Docker公式のUbuntu向けapt repository方式でインストールする。

古いDocker系パッケージがある場合は削除する。

```bash
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
  sudo apt-get remove -y "$pkg" || true
done
```

Docker公式GPGキーとapt repositoryを追加する。

```bash
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Dockerをインストールする。

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

確認する。

```bash
sudo systemctl status docker
sudo docker version
sudo docker compose version
```

正常な結果:

- Docker daemonが起動している。
- `docker compose version` が表示される。

この手順では安全側に倒し、Dockerコマンドは `sudo docker ...` で実行する。

## 9. GitHubからリポジトリをcloneする

```bash
git clone <PUBLIC_REPOSITORY_URL>
cd Cowrie-Honeypot
```

確認する。

```bash
git status --short --branch
ls
```

正常な結果:

- `README.md`、`compose.yaml`、`.env.lightsail.example`、`docs/` が存在する。
- 未コミット変更がない。

## 10. Lightsail用 `.env` を作成する

```bash
cp .env.lightsail.example .env
```

内容を確認する。

```bash
sed -n '1,120p' .env
```

期待する内容:

```dotenv
COWRIE_IMAGE=cowrie/cowrie:latest
COWRIE_SSH_BIND_ADDRESS=0.0.0.0
COWRIE_SSH_PORT=22
TZ=UTC
```

注意:

- `.env` に秘密情報を書かない。
- `.env` はGitへコミットしない。
- 管理用OpenSSHを22番以外へ移してからこの設定を使う。

## 11. Compose設定を確認する

```bash
sudo docker compose config
```

確認ポイント:

- `cowrie-ssh-proxy` が `0.0.0.0:22->2222/tcp` を公開する。
- `cowrie` 本体はホストポートを直接公開していない。
- `cowrie-net` が `internal: true` になっている。
- `logs/cowrie/` と `data/downloads/` がホスト側へマウントされている。

## 12. Cowrieを起動する

```bash
sudo docker compose up -d
sudo docker compose ps
```

正常な結果:

- `cowrie` が起動している。
- `cowrie-ssh-proxy` が起動している。
- `cowrie-ssh-proxy` がTCP 22番を公開している。

ログを確認する。

```bash
sudo docker compose logs --tail=50 cowrie
```

正常な結果:

- CowrieがSSH接続を受け付ける状態になっている。

## 13. 外部からCowrieへ接続する

ローカルPCや別の端末から確認する。

```bash
ssh -p 22 root@<LIGHTSAIL_STATIC_IP>
```

パスワードを聞かれたら、検証用に任意の文字列を入力してよい。Cowrieは観測用の模擬環境である。

確認ポイント:

- 接続先が本物の管理用OpenSSHではなくCowrieである。
- 管理用ユーザー `ubuntu` の本物のシェルに入っていない。
- 入力した内容がCowrieログに記録される。

サーバー側でログを確認する。

```bash
ls -l logs/cowrie
sudo docker compose logs --tail=50 cowrie
```

## 14. 管理用OpenSSHが22番で公開されていないことを確認する

サーバー上で確認する。

```bash
sudo ss -ltnp
```

確認ポイント:

- `sshd` は22222番などの管理用ポートで待ち受けている。
- `sshd` が22番で待ち受けていない。
- 22番を受けているのはDockerのポート公開である。

## 15. Cowrie本体の外向き通信制限を確認する

```bash
./scripts/verify_egress.sh
```

正常な結果:

```text
OK: outbound connection was blocked.
```

`NG: outbound connection succeeded.` が出た場合:

1. Cowrieを停止する。
2. Dockerネットワーク設定を確認する。
3. Lightsailファイアウォールとホスト側制御を見直す。
4. 原因が分かるまで公開運用しない。

停止コマンド:

```bash
sudo docker compose down
```

## 16. Python分析環境を作る

ログ分析をLightsail上でも実行する場合は、プロジェクト直下に `.venv` を作る。

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -e .[dev]
```

集計する。

```bash
./.venv/bin/python -m cowrie_observer.cli analyze --input logs/cowrie/cowrie.json --output data/public/summary.csv
```

確認する。

```bash
sed -n '1,80p' data/public/summary.csv
```

確認ポイント:

- CSVにパスワードが出ていない。
- IPが匿名化されている。
- `data/public/summary.csv` はGitへコミットしない。

## 17. 停止手順

通常停止:

```bash
sudo docker compose down
```

緊急停止:

```bash
sudo docker stop cowrie-ssh-proxy cowrie-observer
```

Lightsail画面で即時遮断する場合:

- TCP 22番のファイアウォールルールを削除する。
- 必要に応じてインスタンスを停止する。

## 18. 復旧手順

```bash
ssh -i /path/to/key.pem -p 22222 ubuntu@<LIGHTSAIL_STATIC_IP>
cd Cowrie-Honeypot
git status --short
sudo docker compose down
sudo docker compose up -d
sudo docker compose ps
./scripts/verify_egress.sh
```

確認ポイント:

- 管理用SSHで入れる。
- Cowrieが22番で受けられる。
- Cowrie本体から外へ出られない。
- ログが残っている。

## 19. 監視するもの

初期運用では次を定期的に確認する。

```bash
df -h
du -sh logs/cowrie data/downloads
sudo docker compose ps
sudo docker compose logs --tail=100 cowrie
```

Lightsail画面で確認するもの:

- 料金アラート
- インスタンス状態
- 静的IPのアタッチ状態
- IPv4ファイアウォール
- IPv6ファイアウォール
- 不要ポートが開いていないこと

## 20. 公開前の最終チェック

Gitへpushする前に、ローカルPCで確認する。

```powershell
git status --short
rg -n "BEGIN|PRIVATE|SECRET|TOKEN|AWS_ACCESS|AKIA|password=|hikar|AppData" README.md AGENTS.md docs src tests scripts .env.example .env.lightsail.example compose.yaml pyproject.toml
```

確認ポイント:

- `.env` がGit差分に入っていない。
- `logs/` がGit差分に入っていない。
- `data/public/summary.csv` がGit差分に入っていない。
- 実IP、秘密鍵、AWS認証情報が入っていない。

## 参考

- Amazon Lightsail: 静的IPはインスタンス停止・再起動時のIP変化を避けるために使う。
- Amazon Lightsail: IPv4ファイアウォールとIPv6ファイアウォールは独立しており、別々に設定する。
- Docker Docs: UbuntuではDocker EngineとCompose pluginを公式apt repositoryから導入する。
