import requests
import json

def get_comments(video_id, key):

    # init get payload
    params = {
        'key': key,
        'videoId': video_id,
        'part': 'snippet,replies',
        'textFormat': 'plainText'
    }
    
    comments = []

    while True:

        # get comments
        response = requests.get("https://www.googleapis.com/youtube/v3/commentThreads", params=params)
        data = response.json()   

        # process comments
        for i in data["items"]:

            snippet = i["snippet"]["topLevelComment"]["snippet"]
            comment = {
                "author": snippet["authorDisplayName"],
                "text": snippet["textDisplay"],
                "timestamp": snippet["publishedAt"],
                "likes": snippet["likeCount"],
                "replies": []
            }

            # process replies
            if "replies" in i:
                for i in i["replies"]["comments"]:

                    snippet = i["snippet"]
                    reply = {
                        "author": snippet["authorDisplayName"],
                        "text": snippet["textDisplay"],
                        "timestamp": snippet["publishedAt"],
                        "likes": snippet["likeCount"]
                    }

                    comment["replies"].append(reply)

            comments.append(comment)
        
        if 'nextPageToken' in data:
            params['pageToken'] = data['nextPageToken']
        else:
            break

    with open(f"youtube/{video_id}_comments.json", 'w') as f:
        json.dump(comments, f, indent=4)