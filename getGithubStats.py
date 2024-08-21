import requests
import datetime
from collections import defaultdict


accessKey = "" # Use your own key....


prDictionary = defaultdict(list)
filteredUsers = ['github-actions[bot]']
filteredTitles = ['Release/']
repos = ['customer-frontend-pwa', 'hubspot', 'module-core', 'db-requests', 'wallet-service', 'investments-service', 'fe-internal', 'component-library', 'wallet-api']

# This will only be for some branches right?
def isRelease(branch, title):
    return (branch == 'master' or branch == 'main') and ('Release' in title  or 'RELEASE' in title)


def getAggregateLinesOfCode(baseUrl, prNumber, headers):
    totalLinesDeleted = 0
    url = f"{baseUrl}/{prNumber}/files"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        for file in data:
            if 'patch' not in file:
                continue
            patchContent = file['patch']
            patchLines = patchContent.split('\n')
            for line in patchLines:
                if line.startswith('+') and not line.startswith('+++') and not line.startswith('++'):
                    totalLinesDeleted -= 1
                if line.startswith('-') and not line.startswith('---') and not line.startswith('--'):
                    totalLinesDeleted += 1
    else:
        print(f"Failed to retrieve files for PR {prNumber}. Status code: {response.status_code}")
        print(response.text)
    return max(totalLinesDeleted, 0)

totalRequestsAllRepos = 0

for repo in repos:
    print(f"\n\n***************Processing repo: {repo}*********************\n\n")
    url = "https://api.github.com/repos/getground/" + repo + "/pulls"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + accessKey,
        "X-GitHub-Api-Version": "2022-11-28"
    }
    page = 1
    created  = None
    minDate = datetime.datetime(2024, 7, 1)
    totalRequests = 0
    while created is None or created >= minDate:
        # Make the API request
        response = requests.get(url, params={ "state": "closed", "sort": "created", "direction": "desc", "page": page, "per_page": "100" }, headers=headers)

        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            for pr in data:
                created = datetime.datetime.strptime(pr['created_at'], "%Y-%m-%dT%H:%M:%SZ")
                user = pr['user']['login']
                baseBranch = pr['base']['ref']
                if not user in filteredUsers and not isRelease(baseBranch, pr['title']) and created >= minDate:
                    # print(f"Title: {pr['title']}, State: {pr['state']}")
                    # print(getAggregateLinesOfCode(url, pr['number'], headers))
                    pr['totalLinesDeleted'] = getAggregateLinesOfCode(url, pr['number'], headers)
                    prDictionary[user].append(pr)
                    totalRequests += 1
                    totalRequestsAllRepos += 1
                else:
                    continue
                    # print(f"Skipping PR: {pr['title']}, User: {user}, Base Branch: {baseBranch}, Created At: {created}")
        else:
            print(f"Failed to retrieve pull requests. Status code: {response.status_code}")
            print(response.text)
        print(f"For repo: {repo}, Finished page: {page}, Total PRs: {totalRequests}, Overall PRs: {totalRequestsAllRepos}")
        page += 1

overallRank = defaultdict(int)

for key in prDictionary:
    prs = prDictionary[key]
    totalLinesDeleted = sum([pr['totalLinesDeleted'] for pr in prs])
    overallRank[key] = totalLinesDeleted
    print("User: " + key + " Total Lines Deleted: " + str(totalLinesDeleted), " Total PRs: " + str(len(prs)))
    
sortedOverallRank = sorted(overallRank.items(), key=lambda x: x[1], reverse=True)
print("\n\n\n")
index = 1
for user, num in sortedOverallRank:
    print(str(index) + ". User: " + user + " Total Lines Deleted: " + str(num))
    index += 1

