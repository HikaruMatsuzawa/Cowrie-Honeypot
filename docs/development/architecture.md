# アーキテクチャ

## 設計ステータス

- 確定: ローカル環境ではCowrieをインターネットへ公開しない。
- 確定: ローカルでは `127.0.0.1:2222` だけをSSH確認用に使う。
- 確定: LightsailではTCP 22番をCowrie観測用SSHとして扱う。
- 確定: 管理用OpenSSHはTCP 22番以外へ移動する。
- 確定: LightsailではCowrieコンテナをホスト側TCP 22番へ直接公開し、実送信元IPをCowrieログへ残す。
- 確定: `cowrie-ssh-proxy` は実送信元IPを失うため、Lightsail運用構成から外す。
- 確定: 生ログはGit管理外とする。
- 確定: CowrieコンテナはDocker internal networkに置く。
- 確定: Lightsailでは追加防御として、Dockerの `DOCKER-USER` chainにiptablesルールを追加する。
- 暫定: LightsailのOSはUbuntu LTSとする。
- 暫定: 管理用OpenSSHのポートは `22222` を例とする。
- 暫定: Dockerネットワークは固定サブネットを使い、ホスト側firewallの対象を安定させる。
- 未決: Lightsailのリージョン、インスタンスサイズ、ディスク容量。
- 未決: 長期ログバックアップ方式。
- 未決: 監視通知先。
- 未決: firewallルールをOS再起動後に永続化する方式。

## ローカル構成

```text
Windows PC
  |
  | 127.0.0.1:2222
  v
Cowrie container:2222
  |
  +-- logs/cowrie/      Git管理外
  +-- data/downloads/   Git管理外
```

ローカルでは `compose.yaml` のみを使用する。

```powershell
docker compose up -d
```

公開範囲:

| ポート | 用途 | 公開範囲 |
| --- | --- | --- |
| TCP 2222 | ローカルCowrie確認 | `127.0.0.1` のみ |
| TCP 22 | 使用しない | 公開しない |
| TCP 23 | 使用しない | 公開しない |

## Lightsail構成

```text
Internet
  |
  | TCP 22
  v
Lightsail instance
  |
  | Docker published port 0.0.0.0:22 -> 2222
  v
Cowrie container:2222
  |
  | outbound traffic blocked by host firewall
  x
Internet

Administrator
  |
  | TCP 22222, 管理者IPのみ
  v
OpenSSH on Lightsail host
```

Lightsailでは `.env.lightsail.example` を `.env` にコピーし、`compose.yaml` を使用する。

```bash
cp .env.lightsail.example .env
sudo docker compose up -d
```

公開範囲:

| ポート | 用途 | 公開範囲 |
| --- | --- | --- |
| TCP 22 | Cowrie観測用SSH | 任意のIPv4 |
| TCP 22222 | 管理用OpenSSH | 管理者IP/32 |
| TCP 23 | Telnet | 公開しない |
| TCP 80/443 | Web | 公開しない |

## コンテナ構成

| サービス | 役割 | ホスト公開 |
| --- | --- | --- |
| `cowrie` | Cowrie本体、ログ生成、SSH観測 | ローカルでは `127.0.0.1:2222`、Lightsailでは `0.0.0.0:22` |

Cowrie本体は外部からのSSH接続を直接受ける。これにより、Cowrieログの `src_ip` に実際の外部送信元IPを残す。

注意: `cowrie-ssh-proxy` でTCP接続を中継する構成では、Cowrieから見た接続元が実際の外部端末IPではなく、proxyコンテナの内部IPになる場合がある。そのため、Lightsail運用では `cowrie-ssh-proxy` を使わない。

Cowrie本体から外部への通信は、Docker internal networkで抑制する。Lightsail Ubuntuでは防御を重ねるため、Dockerが用意する `DOCKER-USER` chainにもiptablesルールを追加し、CowrieコンテナIPから外部への新規通信を拒否する。

## データ配置

| パス | 用途 | Git管理 |
| --- | --- | --- |
| `logs/cowrie/` | Cowrie生ログ | しない |
| `data/downloads/` | Cowrieが取得したファイル | しない |
| `data/public/` | 公開用CSVなどの生成物 | しない |
| `tests/fixtures/` | 合成テストデータ | する |
| `.env` | 実環境設定 | しない |
| `.env.example` | 設定テンプレート | する |

## 分析処理

```text
Cowrie JSON Lines
  |
  v
parser
  |
  v
normalizer
  |
  v
statistics / command classifier / anonymizer
  |
  v
public CSV
```

生ログは上書きしない。公開用CSVを生成するときだけIP匿名化やパスワード除外を適用する。
