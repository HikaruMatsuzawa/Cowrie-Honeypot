# Cowrie-Honeypot

AWS上で安全に運用する，CowrieベースのSSHハニーポット観測システムの文書リポジトリです．

本プロジェクトの目的は，攻撃機能を提供することではなく，外部から届くSSHブルートフォースやLinux/IoT機器を狙うボットの挙動を，低対話型ハニーポットで受動的に記録し，ログを分析することです．

## 文書

- [プロジェクト概要](docs/project-brief.md)
- [要件定義](docs/requirements.md)
- [アーキテクチャ](docs/architecture.md)
- [セキュリティ](docs/security.md)
- [テスト計画](docs/test-plan.md)
- [開発計画](docs/development-plan.md)
- [Codex開発手順](docs/codex-workflow.md)
- [運用手順](docs/operations.md)

## ローカル構成

ローカルのCowrieは `127.0.0.1:2222` のみに公開する設計です．インターネットやLANへ公開しないでください．

設定値が必要な場合は `.env.example` を `.env` へコピーして編集します．`.env` はGitへコミットしません．

```powershell
docker compose config
```

上記で構成を確認できます．コンテナ起動は，内容を確認してから手動で行います．

## ログ分析CLI

Python関連コマンドは `.venv` 経由で実行します．

```powershell
.\.venv\Scripts\python -m cowrie_observer.cli analyze --input <cowrie.jsonl> --output <summary.csv>
```

公開用CSVでは送信元IPを匿名化し，パスワード集計は出力しません．生ログや実IPを含むファイルはGitへコミットしないでください．
