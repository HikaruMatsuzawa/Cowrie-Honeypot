# アーキテクチャ

## 設計ステータス

- 確定: ローカル環境ではCowrieをインターネットへ公開しない。
- 確定: ローカルでは `127.0.0.1:2222` だけをSSH確認用に使う。
- 確定: LightsailではTCP 22番をCowrie観測用SSHとして扱う。
- 確定: 管理用OpenSSHはTCP 22番以外へ移動する。
- 確定: Cowrie本体はDocker内部ネットワークに置く。
- 確定: ホスト側ポートは `cowrie-ssh-proxy` でCowrieへ中継する。
- 確定: 生ログはGit管理外とする。
- 暫定: LightsailのOSはUbuntu LTSとする。
- 暫定: 管理用OpenSSHのポートは `22222` を例とする。
- 暫定: 現在の `cowrie-ssh-proxy` 構成では、Cowrieログ上の送信元IPがproxyコンテナの内部IPになる場合がある。
- 未決: Lightsailのリージョン、インスタンスサイズ、ディスク容量。
- 未決: 長期ログバックアップ方式。
- 未決: 監視通知先。
- 未決: Cowrie本体の外向き通信制限を維持したまま、実際の外部送信元IPをログへ保持する方式。

## ローカル構成

```text
Windows PC
  |
  | 127.0.0.1:2222
  v
cowrie-ssh-proxy
  |
  | Docker internal network
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
  | Docker published port
  v
cowrie-ssh-proxy
  |
  | Docker internal network
  v
Cowrie container:2222

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
| `cowrie` | Cowrie本体、ログ生成 | なし |
| `cowrie-ssh-proxy` | ホスト側SSHポートからCowrieへ中継 | ローカルまたはLightsail用ポート |

Cowrie本体はDocker内部ネットワークにのみ接続し、外部へ直接通信できない状態を目標とする。

注意: `cowrie-ssh-proxy` でTCP接続を中継する構成では、Cowrieから見た接続元が実際の外部端末IPではなく、proxyコンテナの内部IPになる場合がある。認証試行や入力コマンドの観測は可能だが、送信元IP別の分析をAWS運用で正しく行うには、送信元IPを保持できる構成を別途確定する。

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
