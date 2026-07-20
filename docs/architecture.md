# アーキテクチャ

## 設計ステータス

- 確定: ローカルPCではCowrieをインターネットへ公開しない．
- 確定: ローカルではホストのTCP 2222番をCowrieコンテナへ割り当てる．
- 確定: AWSでは本物のOpenSSHをTCP 22番で公開しない．
- 確定: AWSではTCP 22番をCowrie観測用SSHとして扱う．
- 暫定: AWS環境はEC2 1台，Ubuntu，Docker Composeで構成する．
- 暫定: 管理用OpenSSHはTCP 22222番などへ変更し，環境変数またはデプロイ設定で変更可能とする．
- 未決: Cowrieコンテナの外向き通信制限に `internal: true` を採用するかどうか．
- 未決: 外向き通信制限にnftablesとiptablesのどちらを使うか．
- 未決: AWS Systems Manager Session Managerを復旧手段として採用するか．

## ローカル開発環境

ローカルPCではCowrieをインターネットへ公開しない．構成は次のとおりとする．

```text
Windows PC
├─ VS Code
├─ Codex
├─ Git
├─ Docker Desktop
├─ Docker Compose
├─ Cowrieコンテナ
├─ Pythonログ分析プログラム
└─ pytest
```

ローカルでは，ホストのTCP 2222番をCowrieコンテナへ割り当てる．

```text
localhost:2222
      ↓
Dockerポート転送
      ↓
Cowrieコンテナ:2222
```

ローカルテスト時の接続例は次のとおりとする．

```bash
ssh -p 2222 root@localhost
```

ローカルでは，ルーターのポート開放やインターネット公開を行わない．

## AWS環境

AWSでは，EC2上にDocker Compose環境を作成する．

```text
Internet
   │
   ├─ TCP 22
   │     ↓
   │  EC2ホスト
   │     ↓
   │  Dockerポート転送
   │     ↓
   │  Cowrieコンテナ:2222
   │
   └─ TCP 22222
          ↓
       OpenSSH
          ↑
     管理者IPのみ
```

初期バージョンでは，EC2を1台だけ使用する．

```text
EC2
├─ Ubuntu
├─ OpenSSH
├─ Docker
├─ Docker Compose
├─ Cowrie
├─ JSONログ
├─ Python分析プログラム
└─ ログローテーション
```

## ポート設計

### ローカル

| ポート | 用途 | 公開範囲 |
| --- | --- | --- |
| TCP 2222 | Cowrie SSH | localhostのみ |
| TCP 23 | 使用しない | 非公開 |
| その他 | 使用しない | 非公開 |

Docker Composeでは，次の形式を基本とする．

```yaml
ports:
  - "127.0.0.1:2222:2222"
```

ローカルでは `127.0.0.1` へ明示的にバインドし，LAN内の別端末からも接続できないようにする．

ローカルのログ保存先は次のとおりとする．

| ホスト側パス | 用途 | Git管理 |
| --- | --- | --- |
| `logs/cowrie/` | Cowrie JSONログ | 管理しない |
| `data/downloads/` | Cowrieが取得したファイル | 管理しない |

### AWS

| ポート | 用途 | 接続元 |
| --- | --- | --- |
| TCP 22 | Cowrie観測用SSH | 0.0.0.0/0 |
| TCP 22222 | EC2管理用OpenSSH | 管理者のグローバルIP/32 |
| TCP 23 | Telnet | 初期バージョンでは閉鎖 |
| その他 | 不使用 | 拒否 |

CowrieのDockerポート転送は次の形式とする．

```yaml
ports:
  - "22:2222"
```

意味は次のとおりである．

```text
インターネットのTCP 22
        ↓
EC2ホストのTCP 22
        ↓
CowrieコンテナのTCP 2222
```

## 将来の想定ディレクトリ構成

次の構成は将来の想定であり，今回の文書整理ではコード，Docker，deploy配下の実ファイルは作成しない．

```text
cowrie-observer/
├─ AGENTS.md
├─ README.md
├─ compose.yaml
├─ pyproject.toml
├─ .env.example
├─ .gitignore
├─ config/
├─ src/
├─ tests/
├─ deploy/
├─ scripts/
├─ docs/
├─ data/
└─ logs/
```
