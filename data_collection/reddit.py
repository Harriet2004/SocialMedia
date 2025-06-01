from redditClient import redditClient
from collections import deque
from datetime import datetime as dt
from datetime import UTC
import csv
from os import get_terminal_size
from os.path import isfile
import pandas as pd


term_w = get_terminal_size()[0]
total = 0
mod_p = 0
mod_c = 0

def parse_datetime(timestamp):
    return dt.fromtimestamp(timestamp, UTC).strftime('%Y-%m-%d %H:%M:%S')

def process_submission(idx, total_p, submission, limit):

    global total, mod_p, mod_c

    if submission.author and submission.author.name.lower() == "automoderator":
        mod_p += 1
        return []

    rows = [
        [
            submission.id,
            None,
            submission.title,
            submission.author,
            submission.view_count,
            submission.score,
            submission.upvote_ratio,
            parse_datetime(submission.created_utc)
        ]
    ]
    count = 1
    total += 1

    queue = deque()
    queue.extend(submission.comments)

    while queue and count < limit:

        item = queue.popleft()
        item_type = type(item).__name__

        if item_type == "Comment":

            if item.author and item.author.name.lower() == "automoderator":
                mod_c += 1
                continue

            else:

                rows.append([
                    item.id,
                    item.parent_id,
                    item.body,
                    item.author,
                    None,
                    item.score,
                    item.ups,
                    parse_datetime(item.created_utc)
                ])
                
                count += 1
                total += 1

                if (count + len(queue)) < limit:
                    queue.extendleft(reversed(item.replies))

        elif item_type == "MoreComments":

            if (count + len(queue)) < limit:
                queue.extend(item.comments())

        print(f"Fetching submission {idx} out of {total_p} | ID: {submission.id} | comments fetched: {count-1}/{limit} | total fetched: {total} | {idx/total_p*100:.5f}% done | automod filter: posts {mod_p}, comments {mod_c}".ljust(term_w), end = "\r")

    return rows

def fetch(queries, limit, path):

    print("Initializing reddit client...")

    client = redditClient()

    print("Scanning submissions...")
    subreddit = client.subreddit("all")

    submission_ids = set()
    submissions = []
    count_p = []
    count_c = []
    collisions = 0

    for query in queries:

        count_p.append(0)
        count_c.append(0)

        results = subreddit.search(query, sort='relevance', limit=50)

        for submission in results:
            
            if submission.id not in submission_ids:
                
                submission_ids.add(submission.id)
                submissions.append(submission)
                
                count_p[-1] += 1
                count_c[-1] += submission.num_comments

            else:
                collisions += 1

        print(f"Query: {query} | {count_p[-1]} posts | {count_c[-1]} comments")

    total_p = sum(count_p)
    total_c = sum(count_c)    
    scalar = limit / (sum(count_p) + sum(count_c))

    print(f"Total: {total_p} posts | {total_c} comments | scalar: {scalar} (target {limit} rows, {scalar*100:.2f}% of the total content will be fetched)")

    print(f"Collisions: {collisions}")

    collected_submissions = None

    if isfile(path):

        print("File exists, validating contents...")

        try:

            df = pd.read_csv(path)

            last_t3 = [s_id for s_id in df['parent_id'].unique() if str(s_id)[:2] == "t3"][-1]
            start_rm = df[df['parent_id'] == last_t3].index[0]
            df = df.iloc[:start_rm]
            df.to_csv(path, index=False)

            global total
            total = len(df)
        
            collected_submissions = set(df.loc[df['parent_id'].isna(), 'id'])

            print(f"Collected {total} submissions, continuing")

        except Exception:
            
            pass
            
    print(f"Opening file: {path}")

    file = open(path, 'a', encoding="utf-8", newline='')
    writer = csv.writer(file)

    print(collected_submissions)

    if collected_submissions is None:

        writer.writerow(["id", "parent_id", "text", "author", "views", "score", "upvote_ratio", "datetime"])

        for i, submission in enumerate(submissions):
            
            limit = int(submission.num_comments * scalar)
            rows = process_submission(i+1, total_p, submission, limit)
            writer.writerows(rows)

    else:

        for i, submission in enumerate(submissions):

            if submission.id not in collected_submissions:
            
                limit = int(submission.num_comments * scalar)
                rows = process_submission(i+1, total_p, submission, limit)
                writer.writerows(rows)

    print("")