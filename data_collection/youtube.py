import requests
import json
from datetime import datetime as dt
import csv
from os import get_terminal_size

term_w = get_terminal_size()[0]
total_rows = 0
# limit = 25000

stats = {
    "total_videos": 0,
    "collected": 0
}

quota_used = {
    "search": 0,
    "videos": 0,
    "comments": 0
}

def increment_quota(type):
    global quota_used
    if type == "search": quota_used["search"] += 1
    elif type == "videos": quota_used["videos"] += 1
    elif type == "comments": quota_used["comments"] += 1


def datetime_parser(datetime):
    return dt.strptime(datetime, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")


def get_video_ids(query, key):

    params = {
        'key': key,
        'part': 'snippet',
        'type': 'video',
        'q': query,
        'maxResults': 50
    }

    video_ids = []

    response = requests.get("https://www.googleapis.com/youtube/v3/search", params=params)
    increment_quota("search")
    
    url = response.url
    response = response.json()

    if "items" not in response:
        print("Error:", url)
        return []

    for item in response["items"]:     
        if "videoId" in item["id"]:
            video_ids.append(item["id"]["videoId"])

    return video_ids

def process_video(video_id, limit, key):

    global total_rows

    params = {
            'key': key,
            'part': 'snippet,statistics',
            'id': video_id
        }
        
    response = requests.get("https://www.googleapis.com/youtube/v3/videos", params=params)
    increment_quota("videos")

    url = response.url
    response = response.json()
    if "items" not in response:
        print("Error:", url)
        return []

    item = response["items"][0]
    rows = [
        [
            item["id"],
            None,
            item["snippet"]["title"],
            item["snippet"]["channelId"],
            item["statistics"]["viewCount"],
            item["statistics"]["likeCount"] if ("likeCount" in item["statistics"]) else None,
            datetime_parser(item["snippet"]["publishedAt"])
        ]
    ]

    total_rows += 1

    params = {
        'key': key,
        'videoId': video_id,
        'part': 'snippet,replies',
        'textFormat': 'plainText',
        'maxResults': 50
    }

    count_c = 0
    print(f"Processing video: {video_id} | {vc} out of {tv} | ID: {item["id"]} | comments fetched: {count_c}/{limit} | total fetched: {total_rows} | {vc/tv*100:.5f}% done | Quota | Search:{quota_used['search']}, Video:{quota_used['videos']}, Comments:{quota_used['comments']}".ljust(term_w), end = "\r")

    while count_c < limit:
        
        response = requests.get("https://www.googleapis.com/youtube/v3/commentThreads", params=params)
        increment_quota("comments")
        
        url = response.url
        response = response.json()
        if ("error" in response) or ("items" not in response):
            print(url + "\n")
            print("Error:", url)
            exit()
        
        for item in response["items"]:

            # if count_c >= limit: 
            #     return rows

            snippet = item["snippet"]["topLevelComment"]["snippet"]
            rows.append([
                item["id"],
                snippet["videoId"],
                snippet["textOriginal"],
                snippet["authorDisplayName"],
                None,
                snippet["likeCount"],
                datetime_parser(snippet["publishedAt"])
            ])
            count_c += 1
            total_rows += 1

            if "replies" in item:

                for reply in item["replies"]["comments"]:

                    snippet = reply["snippet"]
                    rows.append([
                        reply["id"],
                        snippet["parentId"],
                        snippet["textOriginal"],
                        snippet["authorDisplayName"],
                        None,
                        snippet["likeCount"],
                        datetime_parser(snippet["publishedAt"])
                    ])
                    count_c += 1
                    total_rows += 1

            tv = stats["total_videos"]
            vc = stats["collected"]
            print(f"Processing video: {video_id} | {vc} out of {tv} | ID: {item["id"]} | comments fetched: {count_c}/{limit} | total fetched: {total_rows} | {vc/tv*100:.5f}% done | Quota | Search:{quota_used['search']}, Video:{quota_used['videos']}, Comments:{quota_used['comments']}".ljust(term_w), end = "\r")

        if 'nextPageToken' in response:
            params['pageToken'] = response['nextPageToken']
        else:
            break
        
    return rows

    

def calculate_statistics(video_ids, key):

    total_comment_count = 0
    comment_counts = []

    for video_id in video_ids:

        params = {
            'key': key,
            'part': 'snippet,statistics',
            'id': video_id
        }
        
        response = requests.get("https://www.googleapis.com/youtube/v3/videos", params=params)
        increment_quota("videos")

        url = response.url
        response = response.json()

        try:
            comment_count = int(response["items"][0]["statistics"]["commentCount"])
            total_comment_count += comment_count
            comment_counts.append((video_id, comment_count))
        except (KeyError, IndexError, ValueError):
            print("Error:", url)
            comment_counts.append((video_id, None))

    return len(video_ids), total_comment_count, comment_counts


def fetch(queries, key, limit, path):

    video_ids = set()
    collisions = 0
    count_v = []
    count_c = []

    print("Fetching videos...")

    comment_counts = []

    for query in queries:

        ids = get_video_ids(query, key)
        for id in ids:
            if id not in video_ids:
                video_ids.add(id)
            else:
                collisions += 1
                ids.remove(id)

        v, c, cc = calculate_statistics(ids, key)
        count_v.append(v)
        count_c.append(c)
        comment_counts.extend(cc)

        print(f"Query: {query} | {v} videos, {c} comments")

    total_v = sum(count_v)
    total_c = sum(count_c)

    scalar = limit / (total_c + total_v)

    print("Collissions:", collisions)
    
    print(f"Total | {total_v} videos, {total_c} comments | scalar: {scalar} (target {limit} rows, {scalar*100:.2f}% of the content will be fetched)")
    
    global stats
    stats["total_videos"] = total_v

    file = open(path, 'w', encoding="utf-8", newline='')
    writer = csv.writer(file)
    writer.writerow(["id", "parent_id", "text", "author", "views", "likes", "datetime"])

    for item in comment_counts:

        video_id = item[0]
        stats["collected"] += 1

        limit = int(item[1] * scalar) if item[1] is not None else 0

        rows = process_video(video_id, limit, key)
        writer.writerows(rows)

        print("")