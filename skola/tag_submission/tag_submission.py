from github import Github, Auth
from datetime import datetime, timezone
from dotenv import load_dotenv
import pytz
import os

# Nastavení
load_dotenv()
TOKEN = os.environ["GITHUB_TOKEN"]
ORG_NAME = "oa-pva2-2025-2026"
ASSIGNMENT_NAME = "py-15-parkovaci-automat"
DEADLINE = datetime(2026, 4, 10, 15, 0, 0, tzinfo=pytz.timezone('CET'))
TAG_NAME = "etapa2-deadline-2026-04-10"
TAG_MESSAGE = "Snapshot odevzdání k 10.4.2026 15:00 CET"

# Boti, které ignorovat
BOT_NAMES = {
    "github-classroom[bot]",
    "dependabot[bot]",
    "renovate[bot]",
    "github-actions[bot]",
    "dependabot-preview[bot]"
}


def is_bot_commit(commit):
    """Kontrola, jestli je commit od bota"""
    author_name = commit.commit.author.name.lower()
    return any(bot.lower() in author_name for bot in BOT_NAMES)


def get_user_commits_before_deadline(repo, deadline):
    """Vrací commity od uživatele (ne-bot) před deadlinem"""
    commits = repo.get_commits().reversed  # Od nejstaršího
    user_commits_before = []

    for commit in commits:
        # Preskakuj bot commity
        if is_bot_commit(commit):
            continue

        commit_time = commit.commit.author.date.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone('CET'))

        if commit_time <= deadline:
            user_commits_before.append((commit, commit_time))
        else:
            break  # Už jsou commity po deadlinu

    return user_commits_before


# Připojení k GitHubu
auth = Auth.Token(TOKEN)
g = Github(auth=auth)
org = g.get_organization(ORG_NAME)

print(f"🔍 Hledám repozitáře s '{ASSIGNMENT_NAME}' v organizaci '{ORG_NAME}'...\n")

repos = [repo for repo in org.get_repos() if ASSIGNMENT_NAME in repo.name]
print(f"✅ Našel jsem {len(repos)} repozitářů.\n")

results = []

for repo in repos:
    print(f"📦 {repo.name}...")

    try:
        # Kontrola: existuje už tag?
        try:
            existing_tag = repo.get_git_tag(TAG_NAME)
            status = "⏭️ TAG JIŽ EXISTUJE"
            print(f"   → {status} (skipping)")
            results.append((repo.name, status, None))
            continue
        except:
            # Tag neexistuje, pokračuj dál
            pass

        # Najdi user commity před deadlinem
        user_commits = get_user_commits_before_deadline(repo, DEADLINE)

        if not user_commits:
            status = "❌ NEODEVZDÁNO (bez uživatelských commitů)"
            print(f"   → {status}")
            results.append((repo.name, status, None))
            continue

        # Poslední uživatelský commit před deadlinem
        last_commit_before_deadline, last_commit_timestamp = user_commits[-1]

        # Vytvoř tag
        repo.create_git_tag(
            tag=TAG_NAME,
            message=TAG_MESSAGE,
            object=last_commit_before_deadline.sha,
            type="commit"
        )
        repo.create_git_ref(
            ref=f"refs/tags/{TAG_NAME}",
            sha=last_commit_before_deadline.sha
        )

        status = "✅ TAG VYTVOŘEN"
        author = last_commit_before_deadline.commit.author.name
        print(f"   → {status}")
        print(f"   → Commit: {last_commit_before_deadline.sha[:8]} (od {author})")
        print(f"   → Čas: {last_commit_timestamp.strftime('%d.%m.%Y %H:%M:%S CET')}")
        results.append((repo.name, status, last_commit_timestamp))

    except Exception as e:
        status = f"❌ CHYBA: {str(e)}"
        print(f"   → {status}")
        results.append((repo.name, status, None))

# Souhrn
print("\n" + "=" * 60)
print("SOUHRN")
print("=" * 60)
for repo_name, status, timestamp in results:
    if timestamp:
        print(f"{repo_name:<50} {status} ({timestamp.strftime('%d.%m.%Y %H:%M')})")
    else:
        print(f"{repo_name:<50} {status}")

print(f"\nCelkem zpracováno: {len(results)} repozitářů")
