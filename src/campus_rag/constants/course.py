COURSES_MAX = 3000
MAX_COURSES_PER_FILTER = 6
FILTER_LIMIT = 50
OUTPUT_JSON = """[
  {
      "description": "",
      "courses": [
        "no": 0,  # The index of the course provided above, starting from 0
        "time": [
          {
            "weekday": 1,
            "start": 2,
            "end": 4
          },
          ...
        ],
      ]
  }, 
  {
    ...
  }
]
"""
