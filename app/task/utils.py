from app.models import UserTag

MY_DOC_PIPELINE = [{
    "$project": {
        "id": "$_id",
        "priority": 1,
        "category": 1,
        "theme": 1,
        "tags": 1,
        "comment": 1,
        "update_at": 1,
        "url": 1,
        "create_by": 1,
        "score": {
            "$cond":
            [{
                "$not": "$tags"
            }, 2,
             {
                 "$cond":
                 [{
                     "$in": [UserTag.impressive.value, "$tags"]
                 }, 1,
                  {
                      "$cond": [{
                          "$in": [UserTag.reviewed.value, "$tags"]
                      }, 0,
                                {
                                    "$cond":
                                    [{
                                        "$in": [UserTag.to_do.value, "$tags"]
                                    }, 3, 2]
                                }]
                  }]
             }]
        }
    }
}, {
    "$sort": {
        "score": -1,
        "priority": -1,
        "update_at": -1
    }
}]
