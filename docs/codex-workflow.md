# Codex作業手順

## 目的

この文書は、仕様駆動開発とテスト駆動開発をこのプロジェクトで順番に進めるための手順書である。プロジェクトを十分に理解していない人でも、各Stepのプロンプトを上から順にCodexへ入力し、人間が確認しながら進められるようにする。

## 共通ルール

- 作業前に `README.md`、`AGENTS.md`、関連する `docs/` 配下の仕様書を読む。
- 実装前に、Codexから変更計画、変更予定ファイル、テスト方針、残リスクを提示させる。
- Pythonコマンドは `.venv` を使う。
- 一機能または一作業ごとにコミットする。
- 秘密情報、生ログ、実IP、秘密鍵、`.env`、取得ファイル、生成CSVをコミットしない。
- AWSリソース作成、Lightsailファイアウォール変更、SSH設定変更、IAM変更はCodexに自動実行させない。
- Lightsailへのデプロイは人間が手順を確認して手動で行う。

## Step 1: 仕様書整理

目的: 初期仕様を分割し、開発順序と安全条件を明確にする。

前提条件: 初期仕様書を参照できる。

参照する仕様書: `README.md`, `AGENTS.md`, `docs/project-brief.md`

Codexへ入力するプロンプト:

```text
現在の初期仕様書を、このリポジトリで仕様駆動開発を行うために整理してください。コード、Docker設定、AWS設定は作成しないでください。README、AGENTS、docs配下の仕様書を日本語で整理し、編集前に移動計画、重複、矛盾、確定・暫定・未決、変更予定ファイルを提示してください。
```

変更してよい範囲: `README.md`, `AGENTS.md`, `docs/*.md`

変更してはいけない範囲: コード、Docker設定、AWS設定、SSH設定

実行するテストまたは確認コマンド: Markdownの目視確認、`git status --short`

正常な結果: 指定文書が作成され、内容が日本語で整理されている。

人間が確認するポイント: 元仕様の意味が変わっていないか、危険な操作が含まれていないか。

完了条件: 人間が仕様書構成を承認する。

コミットメッセージ例: `docs: 仕様駆動開発用の初期文書を整理`

次のStepへ進む条件: 開発順序と安全ルールが明確になっている。

## Step 2: Python開発基盤

目的: ログ分析コードをTDDで開発できる最小基盤を作る。

前提条件: Step 1が完了している。

参照する仕様書: `docs/requirements.md`, `docs/test-plan.md`, `docs/security.md`

Codexへ入力するプロンプト:

```text
Step 2「Python開発基盤」だけを実施してください。.venvを使い、pytest、ruff、mypyを実行できる最小構成を作ってください。実装前に計画を提示し、システムPythonへ依存を入れないでください。
```

変更してよい範囲: `pyproject.toml`, `.gitignore`, `src/`, `tests/`

変更してはいけない範囲: Docker設定、AWS設定、実ログ、秘密情報

実行するテストまたは確認コマンド: `pytest`, `ruff check .`, `mypy src`

正常な結果: すべての確認コマンドが成功する。

人間が確認するポイント: 最小構成に留まっているか、公開不要なファイルが含まれていないか。

完了条件: テスト、lint、型チェックが通り、コミットされている。

コミットメッセージ例: `chore: Python開発基盤を追加`

次のStepへ進む条件: `.venv` 前提の開発基盤が動作する。

## Step 3: ローカルCowrie

目的: ローカルPCでインターネットへ公開せずにCowrieを起動できる構成を作る。

前提条件: Docker Desktopを使用できる。

参照する仕様書: `docs/architecture.md`, `docs/security.md`, `docs/operations.md`

Codexへ入力するプロンプト:

```text
Step 3「ローカルCowrie」だけを実施してください。ローカルでは127.0.0.1:2222のみでCowrieへ接続できる構成にしてください。インターネット公開、AWS設定、SSH設定変更は行わないでください。
```

変更してよい範囲: `compose.yaml`, `.env.example`, `config/`, `docs/`

変更してはいけない範囲: AWSリソース、Lightsailファイアウォール、管理用SSH設定、実ログ

実行するテストまたは確認コマンド: `docker compose config`

正常な結果: `127.0.0.1:2222` のみが公開される。

人間が確認するポイント: `0.0.0.0` や22番公開がローカル構成に入っていないか。

完了条件: ローカル起動構成がレビュー可能である。

コミットメッセージ例: `feat: ローカル限定のCowrie構成を追加`

次のStepへ進む条件: ローカル公開範囲が安全である。

## Step 4: ログ永続化

目的: Cowrieログをコンテナ再作成後も残る場所へ保存する。

前提条件: ローカルCowrie構成がある。

参照する仕様書: `docs/requirements.md`, `docs/security.md`, `docs/operations.md`

Codexへ入力するプロンプト:

```text
Step 4「ログ永続化」だけを実施してください。CowrieのJSONログと取得ファイルをホスト側ディレクトリへ保存し、Git管理外にしてください。生ログや取得ファイルをリポジトリへ追加しないでください。
```

変更してよい範囲: `compose.yaml`, `.gitignore`, `docs/`

変更してはいけない範囲: 生ログ、取得ファイル、AWS設定

実行するテストまたは確認コマンド: `docker compose config`, `git check-ignore`

正常な結果: `logs/` と `data/downloads/` がGit管理外である。

人間が確認するポイント: 保存場所と除外設定が十分か。

完了条件: ログ永続化方針が構成と文書に反映されている。

コミットメッセージ例: `feat: Cowrieログ永続化を追加`

次のStepへ進む条件: 生ログがGitに入らない。

## Step 5: JSONログパーサー

目的: Cowrie JSON Linesを安全に読み込む。

前提条件: Python開発基盤がある。

参照する仕様書: `docs/requirements.md`, `docs/test-plan.md`, `docs/security.md`

Codexへ入力するプロンプト:

```text
Step 5「JSONログパーサー」だけをTDDで実施してください。合成fixtureだけを使い、正常行、不正JSON、空行、空ファイル、大きなファイルの逐次処理をテストしてください。
```

変更してよい範囲: `src/`, `tests/`

変更してはいけない範囲: 実ログ、Docker設定、AWS設定

実行するテストまたは確認コマンド: `pytest`, `ruff check .`, `mypy src`

正常な結果: 不正行で処理全体が停止しない。

人間が確認するポイント: 実ログがfixtureに入っていないか。

完了条件: パーサーとテストがコミットされている。

コミットメッセージ例: `feat: Cowrie JSONログパーサーを追加`

次のStepへ進む条件: JSON Linesを逐次処理できる。

## Step 6: 正規化

目的: Cowrieイベントを分析しやすい内部表現へ変換する。

前提条件: JSONログパーサーがある。

参照する仕様書: `docs/requirements.md`, `docs/test-plan.md`

Codexへ入力するプロンプト:

```text
Step 6「正規化」だけをTDDで実施してください。Cowrieイベントから時刻、eventid、src_ip、username、password、session、commandなどを安全に取り出す内部表現を作ってください。
```

変更してよい範囲: `src/`, `tests/`

変更してはいけない範囲: 実ログ、Docker設定、AWS設定

実行するテストまたは確認コマンド: `pytest`, `ruff check .`, `mypy src`

正常な結果: 欠損項目や未知イベントでも処理できる。

人間が確認するポイント: パスワードを不用意に公開出力していないか。

完了条件: 正規化処理とテストがコミットされている。

コミットメッセージ例: `feat: Cowrieイベント正規化を追加`

次のStepへ進む条件: 主要イベントを内部表現へ変換できる。

## Step 7: 集計

目的: 接続数、イベント数、ユーザー名、パスワード、IP、コマンド、セッションを集計する。

前提条件: 正規化処理がある。

参照する仕様書: `docs/requirements.md`, `docs/test-plan.md`

Codexへ入力するプロンプト:

```text
Step 7「集計」だけをTDDで実施してください。総イベント数、接続数、日別・時間帯別接続数、ユーザー名、パスワード、送信元IP、コマンド、セッション別コマンドを集計してください。
```

変更してよい範囲: `src/`, `tests/`

変更してはいけない範囲: 実ログ、Docker設定、AWS設定

実行するテストまたは確認コマンド: `pytest`, `ruff check .`, `mypy src`

正常な結果: 空データ、欠損データ、重複イベントを扱える。

人間が確認するポイント: 集計項目が要件と合っているか。

完了条件: 集計処理とテストがコミットされている。

コミットメッセージ例: `feat: Cowrieイベント集計を追加`

次のStepへ進む条件: 基本集計が再現可能である。

## Step 8: コマンド分類

目的: 入力コマンドをカテゴリへ分類する。

前提条件: 集計処理がある。

参照する仕様書: `docs/requirements.md`, `docs/security.md`, `docs/test-plan.md`

Codexへ入力するプロンプト:

```text
Step 8「コマンド分類」だけをTDDで実施してください。分類ルールは設定または独立モジュールとして管理し、ログ文字列をシェルコマンドとして実行しないでください。
```

変更してよい範囲: `src/`, `tests/`, 必要な設定ファイル

変更してはいけない範囲: 実ログ、攻撃ログ内URLへのアクセス、Docker設定、AWS設定

実行するテストまたは確認コマンド: `pytest`, `ruff check .`, `mypy src`

正常な結果: 主要コマンドをカテゴリ分類でき、未知コマンドは不明として扱う。

人間が確認するポイント: 危険な文字列処理がないか。

完了条件: 分類処理とテストがコミットされている。

コミットメッセージ例: `feat: 入力コマンド分類を追加`

次のStepへ進む条件: 分類結果が仕様に合う。

## Step 9: 匿名化

目的: 公開用データから送信元IPなどの識別情報を匿名化する。

前提条件: 集計処理がある。

参照する仕様書: `docs/requirements.md`, `docs/security.md`

Codexへ入力するプロンプト:

```text
Step 9「匿名化」だけをTDDで実施してください。生ログは上書きせず、公開用データにだけ匿名化を適用してください。IPv4とIPv6をテストしてください。
```

変更してよい範囲: `src/`, `tests/`

変更してはいけない範囲: 生ログ、実IPを含むfixture、AWS設定

実行するテストまたは確認コマンド: `pytest`, `ruff check .`, `mypy src`

正常な結果: 生ログは保持し、公開用データだけ匿名化される。

人間が確認するポイント: 匿名化前後のデータを混在させていないか。

完了条件: 匿名化処理とテストがコミットされている。

コミットメッセージ例: `feat: 公開用データのIP匿名化を追加`

次のStepへ進む条件: 公開用出力に実IPが出ない。

## Step 10: CSVとCLI

目的: 分析結果をCLIからCSVへ出力できるようにする。

前提条件: 集計と匿名化がある。

参照する仕様書: `docs/requirements.md`, `docs/test-plan.md`, `docs/security.md`

Codexへ入力するプロンプト:

```text
Step 10「CSVとCLI」だけをTDDで実施してください。Cowrieログを入力し、匿名化済みの公開用CSVを出力するCLIを作ってください。パスワード情報はCSVへ出力しないでください。
```

変更してよい範囲: `src/`, `tests/`, `scripts/`, `README.md`

変更してはいけない範囲: 実ログ、生成CSVのコミット、Docker設定、AWS設定

実行するテストまたは確認コマンド: `pytest`, `ruff check .`, `mypy src`, CLI実行

正常な結果: CSVを生成でき、秘密情報が出力されない。

人間が確認するポイント: CSV項目が公開可能か。

完了条件: CLIとテストがコミットされている。

コミットメッセージ例: `feat: 分析CSV出力とCLIを追加`

次のStepへ進む条件: 公開用CSVを再現可能に生成できる。

## Step 11: 外向き通信制限

目的: Cowrie本体から外部へ通信できない構成を作る。

前提条件: ローカルCowrieとログ永続化がある。

参照する仕様書: `docs/architecture.md`, `docs/security.md`, `docs/operations.md`

Codexへ入力するプロンプト:

```text
Step 11「外向き通信制限」だけを実施してください。Cowrie本体から外部へ接続できない構成と検証手順を整えてください。インターネット公開やAWS操作は行わないでください。
```

変更してよい範囲: `compose.yaml`, `scripts/`, `docs/`

変更してはいけない範囲: Lightsailファイアウォール、管理用SSH設定、AWSリソース、外向き通信を広げる変更

実行するテストまたは確認コマンド: `docker compose config`, `scripts/verify_egress.ps1`, `scripts/verify_egress.sh`

正常な結果: Cowrie本体から外部通信できない。

人間が確認するポイント: 確認対象がプロキシではなくCowrie本体になっているか。

完了条件: 設定、検証スクリプト、文書がコミットされている。

コミットメッセージ例: `security: Cowrie本体の外向き通信制限を追加`

次のStepへ進む条件: 外向き通信制限が実通信で確認済みである。

## Step 12: ローカル統合テスト

目的: ローカルで観測からCSV出力までを一連の流れとして確認する。

前提条件: Step 1からStep 11が完了している。

参照する仕様書: `docs/test-plan.md`, `docs/architecture.md`, `docs/security.md`, `docs/operations.md`

Codexへ入力するプロンプト:

```text
Step 12「ローカル統合テスト」を実施してください。Dockerを起動してよいか確認したうえで、ローカルCowrie接続、ログ生成、CSV生成、外向き通信制限を確認してください。AWS操作やインターネット公開は行わないでください。
```

変更してよい範囲: テスト補助スクリプト、README、docs、必要最小限のローカル設定修正

変更してはいけない範囲: AWSリソース、Lightsailファイアウォール、管理用SSH設定、実ログや生成CSVのコミット

実行するテストまたは確認コマンド: `pytest`, `ruff check .`, `mypy src`, `docker compose config`, SSH接続確認、CLI実行、外向き通信確認

正常な結果: ローカル統合テストが成功する。

人間が確認するポイント: ローカル以外に公開されていないか、生成物がGitに入っていないか。

完了条件: 結果と残リスクがREADMEまたはdocsに反映され、コミットされている。

コミットメッセージ例: `test: ローカル統合確認手順を追加`

次のStepへ進む条件: 人間がLightsail準備へ進むことを承認する。

## Step 13: AWS Lightsail

目的: Lightsailで手動デプロイ、停止、復旧、監視、受け入れ確認を行える手順を整える。

前提条件: ローカル統合テストが完了している。

参照する仕様書: `docs/project-brief.md`, `docs/requirements.md`, `docs/architecture.md`, `docs/security.md`, `docs/test-plan.md`, `docs/operations.md`, `docs/lightsail-setup.md`

Codexへ入力するプロンプト:

```text
Step 13「AWS Lightsail」を実施してください。AWSリソース作成や設定変更は実行せず、Lightsailへ手動デプロイするための手順、チェックリスト、停止、復旧、監視、受け入れテストを整理してください。README / operations / security がGitHub clone後に迷わず使える内容かレビューし、必要な文書とテンプレートだけを更新してください。
```

変更してよい範囲: `README.md`, `AGENTS.md`, `docs/`, `.env.example`, `.env.lightsail.example`, 必要な設定テンプレート

変更してはいけない範囲: AWSリソース作成、AWS CLI実行、Lightsailファイアウォール変更、SSH設定変更、本番環境でのコマンド実行、秘密情報

実行するテストまたは確認コマンド: `docker compose config`, `docker compose --env-file .env.lightsail.example config`, `pytest`, `ruff check .`, `mypy src`, 公開NG文字列の検索

正常な結果: Lightsail用設定が `0.0.0.0:22` を公開し、ローカル用設定は `127.0.0.1:2222` のままである。

人間が確認するポイント: `docs/lightsail-setup.md` が初回SSHログイン後から迷わず進められるか、管理用OpenSSH移動、Lightsailファイアウォール、静的IP、IPv6、料金、停止手順、復旧手順が明確か。

完了条件: Lightsail手順が文書化され、人間が手動で実施できる状態でコミットされている。

コミットメッセージ例: `docs: Lightsailデプロイ手順を整理`

次のStepへ進む条件: このStepが最終Stepである。次は人間によるLightsail手動デプロイ、または追加Issue計画へ進む。
