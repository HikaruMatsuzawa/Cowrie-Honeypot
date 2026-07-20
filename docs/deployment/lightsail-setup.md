# Lightsail初回セットアップ手順

## 目的

この文書は、まっさらなAmazon LightsailのUbuntuインスタンスへSSHログインできた状態から、Cowrieハニーポットを安全に公開するまでの手順をまとめたものである。

この手順では、次の状態を目標にする。

- 管理用OpenSSHはTCP 22番で公開しない。
- 管理用OpenSSHは管理者IPからのみ接続できる。
- インターネットからTCP 22番へ接続するとCowrieへ到達する。
- Cowrie本体はDocker内部ネットワークに置き、外向き通信できない。
- HTTP、HTTPS、Telnetなど不要なポートは開けない。
- IPv6を使わない場合は、IPv6側も閉じる。
- 生ログ、秘密鍵、`.env`、実IPをGitへ載せない。

## 作業場所の見分け方

各手順の先頭に、どこで作業するかを書く。

| 表記 | 作業する場所 |
| --- | --- |
| Web画面 | AWS Lightsailのブラウザ画面 |
| サーバーSSH | LightsailインスタンスへSSHログインしたターミナル |
| ローカルPC | 自分のPCのPowerShell、ターミナル、または別端末 |

特に危険なのは、Web画面のファイアウォール変更と、サーバーSSHのOpenSSH設定変更である。この2つは順番を飛ばさない。

## 全体の流れ

1. Web画面で静的IPを設定する。
2. Web画面で初期ファイアウォールを安全側へ寄せる。
3. サーバーへSSHログインする。
4. サーバー側のOpenSSHを22番以外へ移す。
5. 新しい管理用SSHポートでログインできることを確認する。
6. Web画面でファイアウォールを最終形にする。
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

実際のIPアドレス、秘密鍵パス、AWSアカウント情報は、README、docs、Issue、コミットに貼らない。

## 0. 管理者のグローバルIPを確認する

作業場所: ローカルPC

Lightsailファイアウォールに設定する管理者IPは、PCのプライベートIPではなく、インターネット側から見えているグローバルIPv4アドレスである。

使わない値:

```text
192.168.x.x
10.x.x.x
172.16.x.x から 172.31.x.x
```

これらは家庭内LANやマンションWi-Fi内のプライベートIPであり、Lightsailの接続元制限には使わない。

ブラウザで確認する場合:

```text
https://checkip.amazonaws.com/
```

PowerShellで確認する場合:

```powershell
(Invoke-WebRequest -UseBasicParsing https://checkip.amazonaws.com/).Content.Trim()
```

LinuxまたはmacOSで確認する場合:

```bash
curl https://checkip.amazonaws.com/
```

表示されたIPv4アドレスに `/32` を付けた値を、Lightsailファイアウォールの管理用SSHルールに使う。

例:

```text
checkip.amazonaws.com の表示: 203.0.113.10
Lightsailに入力する値: 203.0.113.10/32
```

注意:

- 実際に表示されたIPアドレスはGitへコミットしない。
- マンションWi-Fiや家庭回線では、このIPが変わることがある。
- SSH接続できなくなった場合は、もう一度現在のグローバルIPを確認し、Lightsailファイアウォールの管理用SSHルールだけを更新する。
- CGNAT環境では、同じグローバルIPを他の利用者と共有している可能性がある。その場合でも `0.0.0.0/0` に開けっぱなしにするより安全だが、鍵認証のみ、パスワード認証無効化を必ず守る。
- 管理用OpenSSHを任意のIPv4アドレスへ常時公開しない。

## 1. 静的IPを設定する

作業場所: Web画面

Lightsailの動的パブリックIPは、インスタンスの停止や再起動で変わる可能性がある。観測先を固定するため、先に静的IPを作成してインスタンスへアタッチする。

画面操作:

1. Lightsailコンソールを開く。
2. 左メニューまたは上部メニューから `Networking` を開く。
3. `Create static IP` を選ぶ。
4. 対象インスタンスと同じリージョンを選ぶ。
5. 対象インスタンスへ静的IPをアタッチする。
6. 静的IPを控える。

確認ポイント:

- 静的IPが対象インスタンスへアタッチされている。
- 以降の接続先は動的IPではなく静的IPを使う。

## 2. 初期ファイアウォールを設定する

作業場所: Web画面

最初は管理用OpenSSHがTCP 22番で待ち受けている可能性がある。いきなり22番をCowrieへ渡すと、サーバーへ入れなくなる危険がある。

まずは、Step 0で確認した `<YOUR_GLOBAL_IP>/32` だけから管理用SSHへ接続できる状態にする。そのうえで、管理用OpenSSHの移動先としてTCP `22222` を追加する。同時に、不要なHTTPとIPv6側の開放を閉じる。

### スクリーンショットの状態から変更する場合

スクリーンショットでは、次の状態になっている。

IPv4ファイアウォール:

| 行 | 現在の状態 | 操作 |
| --- | --- | --- |
| SSH / TCP / 22 / 任意のIPv4アドレス | 管理用SSHが全世界へ開いている | 鉛筆アイコンで編集し、接続元を `<YOUR_GLOBAL_IP>/32` に変更する |
| HTTP / TCP / 80 / 任意のIPv4アドレス | HTTPが全世界へ開いている | ゴミ箱アイコンで削除する |

IPv6ネットワーキング:

| 行または項目 | 現在の状態 | 操作 |
| --- | --- | --- |
| IPv6ネットワーキング | 有効 | 初期運用では無効化を推奨する |
| IPv6 SSH / TCP / 22 / 任意のIPv6アドレス | IPv6側のSSHが全世界へ開いている | IPv6を無効化しない場合はゴミ箱アイコンで削除する |
| IPv6 HTTP / TCP / 80 / 任意のIPv6アドレス | IPv6側のHTTPが全世界へ開いている | IPv6を無効化しない場合はゴミ箱アイコンで削除する |

### 具体的な画面操作

1. Lightsailインスタンス詳細画面を開く。
2. `Networking` タブを開く。
3. `IPv4 ファイアウォール` を見る。
4. `SSH / TCP / 22` の行の鉛筆アイコンを押す。
5. 接続元を `任意のIPv4アドレス` から、Step 0で確認した `<YOUR_GLOBAL_IP>/32` に変更して保存する。
6. `HTTP / TCP / 80` の行のゴミ箱アイコンを押して削除する。
7. `ルールを追加` を押す。
8. アプリケーションは `カスタム`、プロトコルは `TCP`、ポートは `22222`、制限は Step 0で確認した `<YOUR_GLOBAL_IP>/32` にして追加する。
9. `IPv6 ネットワーキング` が有効な場合、使わないなら無効化する。
10. IPv6を無効化しない場合は、`IPv6 ファイアウォール` の `SSH / TCP / 22` と `HTTP / TCP / 80` を削除する。

初期ファイアウォールの完成形:

| 用途 | プロトコル | ポート | 接続元 |
| --- | --- | --- | --- |
| 初期管理用OpenSSH | TCP | 22 | `<YOUR_GLOBAL_IP>/32` |
| 新管理用OpenSSH | TCP | 22222 | `<YOUR_GLOBAL_IP>/32` |

注意:

- この段階では、22番はまだ管理用OpenSSH用である。
- 22番をCowrie用として全体公開するのは、22222番で管理ログインできることを確認した後である。
- 自宅やマンションの回線でグローバルIPが変わった場合は、22番と22222番の管理用SSH接続元を新しい `<YOUR_GLOBAL_IP>/32` に更新する。
- HTTP 80番はこのプロジェクトでは使わないため削除する。
- 管理用OpenSSHを `0.0.0.0/0` へ開けない。
- LightsailのIPv4ファイアウォールとIPv6ファイアウォールは独立しているため、両方を見る。
- LightsailブラウザSSHは22番の管理用SSHに依存する場合がある。OpenSSHを移動した後は、ローカルPCから22222番で入れることを優先して確認する。

## 3. サーバーへSSHログインする

作業場所: ローカルPC、またはWeb画面のブラウザSSH

ローカルPCから接続する例:

```bash
ssh -i /path/to/key.pem -p 22 ubuntu@<LIGHTSAIL_STATIC_IP>
```

LightsailのブラウザSSHを使ってもよい。

確認ポイント:

- `ubuntu` ユーザーでログインできる。
- この時点では既存のSSHセッションを閉じない。

## 4. 管理用OpenSSHを22番以外へ移す

作業場所: サーバーSSH

現在の待ち受け状態を確認する。

```bash
sudo ss -ltnp | grep sshd
```

OpenSSHが認識しているポートを確認する。

```bash
sudo sshd -T | grep '^port '
```

設定ファイルをバックアップする。

```bash
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
```

設定ファイルを編集する。

```bash
sudo sudoedit /etc/ssh/sshd_config
```

設定例:

```text
Port 22222
PasswordAuthentication no
PermitRootLogin no
```

注意:

- `Port 22` が残っていると、OpenSSHが22番でも待ち受ける可能性がある。
- 設定ファイルが `/etc/ssh/sshd_config.d/` 配下で分割されている環境では、重複する `Port` 設定がないか確認する。

設定構文を確認する。

```bash
sudo sshd -t
```

エラーがなければOpenSSHを反映する。

UbuntuのLightsailイメージでは、OpenSSHがsystemd socket activationで起動している場合がある。この場合、`Port`、`AddressFamily`、`ListenAddress` の変更は `ssh` サービスのreloadだけでは反映されない。

```bash
sudo systemctl daemon-reload
sudo systemctl restart ssh.socket
sudo systemctl restart ssh
```

反映後、待ち受けポートを確認する。

```bash
sudo ss -ltnp | grep sshd
```

正常な結果:

```text
LISTEN ... 0.0.0.0:22222 ...
LISTEN ... [::]:22222 ...
```

`sudo ss -tunap | grep sshd` で確認した場合、既存の22番SSH接続が残っている間は、次のように `ESTAB` として22番が表示されることがある。

```text
tcp LISTEN ... 0.0.0.0:22222 ...
tcp ESTAB  ... 172.x.x.x:22 <YOUR_GLOBAL_IP>:xxxxx ...
tcp LISTEN ... [::]:22222 ...
```

この場合、22番の `ESTAB` は「今開いている管理用SSHセッション」であり、新規待ち受けではない。`LISTEN` が22222番になっていれば、OpenSSHの待ち受けポート変更は反映されている。

もしまだ `0.0.0.0:22` または `[::]:22` だけが表示される場合は、`sshd_config` の `Port 22222` が反映されていない。現在のSSHセッションは閉じずに、次を確認する。

```bash
systemctl list-units --type=service | grep ssh
systemctl list-units --type=socket | grep ssh
sudo grep -R "^Port" /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf 2>/dev/null
```

重要:

- 新しい接続が成功するまで、現在のSSHセッションを閉じない。
- `sshd -t` が失敗した状態で再読み込みや再起動をしない。
- 22番をCowrieへ渡す前に、必ず22222番でログインできることを確認する。

## 5. 新しい管理用SSHポートで接続確認する

作業場所: ローカルPC

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
- `LISTEN` 状態のOpenSSHが22番で待ち受けていない。
- 既存セッションが残っている場合だけ、22番が `ESTAB` 状態で表示されることがある。

## 6. ファイアウォールを最終形にする

作業場所: Web画面

22222番で管理ログインできることを確認できたら、22番をCowrie用にする。

### IPv4ファイアウォールの最終形

| 用途 | プロトコル | ポート | 接続元 |
| --- | --- | --- | --- |
| Cowrie観測用SSH | TCP | 22 | 任意のIPv4アドレス |
| 管理用OpenSSH | TCP | 22222 | `<YOUR_GLOBAL_IP>/32` |

画面操作:

1. `IPv4 ファイアウォール` の `SSH / TCP / 22` の行を確認する。
2. この時点では22番はCowrie用にするため、接続元を `任意のIPv4アドレス` にする。
3. `カスタム / TCP / 22222` の行を確認する。
4. 22222番の接続元は `<YOUR_GLOBAL_IP>/32` のままにする。
5. `HTTP / TCP / 80` が残っていたら削除する。
6. `HTTPS / TCP / 443` や `Telnet / TCP / 23` があれば削除する。
7. その他、用途が説明できないルールは削除する。

### IPv6ファイアウォールの最終形

初期運用ではIPv6を使わない方針を推奨する。

推奨設定:

- `IPv6 ネットワーキング` を無効化する。
- 無効化しない場合でも、`IPv6 ファイアウォール` の `SSH / TCP / 22` と `HTTP / TCP / 80` は削除する。
- IPv6でCowrieを公開する設計は、別途仕様化してから行う。

確認ポイント:

- 管理用OpenSSHは管理者IPからのみ接続できる。
- 管理用OpenSSHを `0.0.0.0/0` へ開けていない。
- TCP 22番はCowrie用として開ける。
- TCP 23番は開けない。
- TCP 80番は開けない。
- IPv6側に `SSH / TCP / 22 / 任意のIPv6アドレス` や `HTTP / TCP / 80 / 任意のIPv6アドレス` が残っていない。

## 7. サーバーの基本パッケージを更新する

作業場所: サーバーSSH

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y ca-certificates curl git
```

確認ポイント:

- エラーなく完了する。
- 再起動が必要と表示された場合は、管理用SSHで再接続できることを確認してから再起動する。

## 8. Docker EngineとCompose pluginをインストールする

作業場所: サーバーSSH

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

作業場所: サーバーSSH

```bash
# git clone <PUBLIC_REPOSITORY_URL>
git clone https://github.com/HikaruMatsuzawa/Cowrie-Honeypot.git
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

作業場所: サーバーSSH

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

作業場所: サーバーSSH

```bash
sudo docker compose config
```

確認ポイント:

- `cowrie-ssh-proxy` が `0.0.0.0:22->2222/tcp` を公開する。
- `cowrie` 本体はホストポートを直接公開していない。
- `cowrie-net` が `internal: true` になっている。
- `logs/cowrie/` と `data/downloads/` がホスト側へマウントされている。

## 12. Cowrieを起動する

作業場所: サーバーSSH

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

作業場所: ローカルPC、または別の外部端末

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

作業場所: サーバーSSH

```bash
sudo ss -ltnp
```

確認ポイント:

- `sshd` は22222番などの管理用ポートで待ち受けている。
- `sshd` が22番で待ち受けていない。
- 22番を受けているのはDockerのポート公開である。

## 15. Cowrie本体の外向き通信制限を確認する

作業場所: サーバーSSH

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

作業場所: サーバーSSH

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

作業場所: サーバーSSH、またはWeb画面

通常停止:

```bash
sudo docker compose down
```

緊急停止:

```bash
sudo docker stop cowrie-ssh-proxy cowrie-observer
```

Web画面で即時遮断する場合:

- LightsailファイアウォールからTCP 22番のルールを削除する。
- 必要に応じてインスタンスを停止する。

## 18. 復旧手順

作業場所: サーバーSSH

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

作業場所: サーバーSSH、Web画面

サーバー上で確認する。

```bash
df -h
du -sh logs/cowrie data/downloads
sudo docker compose ps
sudo docker compose logs --tail=100 cowrie
```

Lightsail画面で確認する。

- 料金アラート
- インスタンス状態
- 静的IPのアタッチ状態
- IPv4ファイアウォール
- IPv6ファイアウォール
- 不要ポートが開いていないこと

## 20. 公開前の最終チェック

作業場所: ローカルPC

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
