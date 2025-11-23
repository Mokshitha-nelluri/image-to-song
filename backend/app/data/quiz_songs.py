"""
Quiz song database - curated songs with preview URLs and audio features.
Used for the music preference quiz system.
"""
from typing import List, Dict, Any

# Quiz song database - curated songs with preview URLs
QUIZ_SONGS: List[Dict[str, Any]] = [
    # Pop (4 songs)
    {
        "id": "4uLU6hMCjMI75M1A2tKUQC",
        "title": "Anti-Hero",
        "artist": "Taylor Swift",
        "album": "Midnights",
        "genres": ["pop", "indie pop"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",  # Will be updated with real URLs
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273bb54dde68cd23e2a268ae0f5",
        "audio_features": {
            "danceability": 0.579,
            "energy": 0.513,
            "valence": 0.321,
            "acousticness": 0.257,
            "instrumentalness": 0.000001,
            "tempo": 96.881,
            "loudness": -8.6
        }
    },
    {
        "id": "1BxfuPKGuaTgP7aM0Bbdwr",
        "title": "Cruel Summer",
        "artist": "Taylor Swift",
        "album": "Lover",
        "genres": ["pop", "synth-pop"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273e787cffec20aa2a396a61647",
        "audio_features": {
            "danceability": 0.552,
            "energy": 0.702,
            "valence": 0.564,
            "acousticness": 0.117,
            "instrumentalness": 0.000096,
            "tempo": 169.994,
            "loudness": -5.707
        }
    },
    {
        "id": "4Dvkj6JhhA12EX05fT7y2e",
        "title": "As It Was",
        "artist": "Harry Styles",
        "album": "Harry's House",
        "genres": ["pop", "art pop"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b2732e8ed79e177ff6011076f5f0",
        "audio_features": {
            "danceability": 0.685,
            "energy": 0.549,
            "valence": 0.359,
            "acousticness": 0.361,
            "instrumentalness": 0.000003,
            "tempo": 108.009,
            "loudness": -7.667
        }
    },
    {
        "id": "7qiZfU4dY1lWllzX7mPBI3",
        "title": "Shape of You",
        "artist": "Ed Sheeran",
        "album": "÷ (Divide)",
        "genres": ["pop", "dance pop"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273ba5db46f4b838ef6027e6f96",
        "audio_features": {
            "danceability": 0.825,
            "energy": 0.652,
            "valence": 0.931,
            "acousticness": 0.581,
            "instrumentalness": 0.000002,
            "tempo": 95.977,
            "loudness": -3.183
        }
    },
    
    # Rock (3 songs)
    {
        "id": "0VjIjW4GlULA4LGy1nby9d",
        "title": "Bohemian Rhapsody",
        "artist": "Queen",
        "album": "A Night at the Opera",
        "genres": ["rock", "classic rock"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273e319baafd16e84f0408af2a0",
        "audio_features": {
            "danceability": 0.495,
            "energy": 0.618,
            "valence": 0.579,
            "acousticness": 0.213,
            "instrumentalness": 0.001,
            "tempo": 144.077,
            "loudness": -8.235
        }
    },
    {
        "id": "4VqPOruhp5EdPBeR92t6lQ",
        "title": "Stairway to Heaven",
        "artist": "Led Zeppelin",
        "album": "Led Zeppelin IV",
        "genres": ["rock", "hard rock"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b2732ac77543e4dd391bfb3a93b6",
        "audio_features": {
            "danceability": 0.378,
            "energy": 0.541,
            "valence": 0.446,
            "acousticness": 0.309,
            "instrumentalness": 0.274,
            "tempo": 81.995,
            "loudness": -14.123
        }
    },
    {
        "id": "0JiV5NKJP0vC8hOJKWMJ7y",
        "title": "Don't Stop Believin'",
        "artist": "Journey",
        "album": "Escape",
        "genres": ["rock", "arena rock"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b2732e77e624a0225686f4e62af6",
        "audio_features": {
            "danceability": 0.563,
            "energy": 0.736,
            "valence": 0.899,
            "acousticness": 0.00131,
            "instrumentalness": 0.000014,
            "tempo": 119.069,
            "loudness": -6.011
        }
    },
    
    # Hip-Hop (3 songs)
    {
        "id": "6DCZcSspjsKoFjzjrWoCdn",
        "title": "God's Plan",
        "artist": "Drake",
        "album": "Scorpion",
        "genres": ["hip hop", "pop rap"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273f907de96b9a4fbc04accc0d5",
        "audio_features": {
            "danceability": 0.754,
            "energy": 0.449,
            "valence": 0.357,
            "acousticness": 0.00685,
            "instrumentalness": 0.000001,
            "tempo": 77.169,
            "loudness": -9.211
        }
    },
    {
        "id": "7ouMYWpwJ422jRcDASZB7P",
        "title": "HUMBLE.",
        "artist": "Kendrick Lamar",
        "album": "DAMN.",
        "genres": ["hip hop", "conscious rap"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b2738b52c6b9bc4e43d873869699",
        "audio_features": {
            "danceability": 0.904,
            "energy": 0.621,
            "valence": 0.421,
            "acousticness": 0.000548,
            "instrumentalness": 0.000024,
            "tempo": 150.020,
            "loudness": -6.842
        }
    },
    {
        "id": "5W3cjX2J3tjhG8zb6u0qHn",
        "title": "Old Town Road",
        "artist": "Lil Nas X",
        "album": "7 EP",
        "genres": ["hip hop", "country rap"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273a5c40298ab23da2ac819f9ab",
        "audio_features": {
            "danceability": 0.876,
            "energy": 0.555,
            "valence": 0.687,
            "acousticness": 0.132,
            "instrumentalness": 0.000003,
            "tempo": 136.041,
            "loudness": -8.871
        }
    },
    
    # Electronic (2 songs)
    {
        "id": "4Y7KDMX07MCuZo10LPW60s",
        "title": "Clarity",
        "artist": "Zedd",
        "album": "Clarity",
        "genres": ["electronic", "progressive house"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b27331c35347e0ec535429c0addc",
        "audio_features": {
            "danceability": 0.473,
            "energy": 0.793,
            "valence": 0.394,
            "acousticness": 0.000234,
            "instrumentalness": 0.000001,
            "tempo": 128.026,
            "loudness": -4.669
        }
    },
    {
        "id": "1vYXt7VSjH9JIM5oewBZNF",
        "title": "Midnight City",
        "artist": "M83",
        "album": "Hurry Up, We're Dreaming",
        "genres": ["electronic", "synthwave"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273bb0e9b14abea7d52e3f7ad58",
        "audio_features": {
            "danceability": 0.511,
            "energy": 0.789,
            "valence": 0.749,
            "acousticness": 0.000069,
            "instrumentalness": 0.893,
            "tempo": 104.896,
            "loudness": -6.398
        }
    },
    
    # Indie (2 songs)
    {
        "id": "2Z8WuEywRWYTKe1NybPQEW",
        "title": "Somebody That I Used to Know",
        "artist": "Gotye",
        "album": "Making Mirrors",
        "genres": ["indie", "alternative"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273f9c35bd8b2fbb68b90b7bbc6",
        "audio_features": {
            "danceability": 0.684,
            "energy": 0.449,
            "valence": 0.425,
            "acousticness": 0.102,
            "instrumentalness": 0.000063,
            "tempo": 129.874,
            "loudness": -7.883
        }
    },
    {
        "id": "0VE4kBnHJEhHWW8nnB2OAJ",
        "title": "Young Folks",
        "artist": "Peter Bjorn and John",
        "album": "Writer's Block",
        "genres": ["indie", "indie pop"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273abc34a5e2c52ec8f3b5ddd35",
        "audio_features": {
            "danceability": 0.728,
            "energy": 0.712,
            "valence": 0.819,
            "acousticness": 0.186,
            "instrumentalness": 0.105,
            "tempo": 120.047,
            "loudness": -6.895
        }
    },
    
    # R&B (2 songs)
    {
        "id": "7dt6x5M1jzdTEt8oCbisTK",
        "title": "Redbone",
        "artist": "Childish Gambino",
        "album": "Awaken, My Love!",
        "genres": ["r&b", "funk"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b2733b5e11ca1b063583df9492db",
        "audio_features": {
            "danceability": 0.738,
            "energy": 0.345,
            "valence": 0.467,
            "acousticness": 0.423,
            "instrumentalness": 0.000017,
            "tempo": 158.784,
            "loudness": -14.558
        }
    },
    {
        "id": "4rXVn5n57hCcKXJ5ZQeaB9",
        "title": "Blinding Lights",
        "artist": "The Weeknd",
        "album": "After Hours",
        "genres": ["r&b", "synthwave"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b2738863bc11d2aa12b54f5aeb36",
        "audio_features": {
            "danceability": 0.514,
            "energy": 0.73,
            "valence": 0.334,
            "acousticness": 0.00146,
            "instrumentalness": 0.000002,
            "tempo": 171.009,
            "loudness": -5.934
        }
    },
    
    # Country (2 songs)
    {
        "id": "1Je1IMUlBXcx1Fz0WE7oPT",
        "title": "Cruise",
        "artist": "Florida Georgia Line",
        "album": "Here's to the Good Times",
        "genres": ["country", "country pop"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273f9b8b5f60b6b2bb5f9b8b5f6",
        "audio_features": {
            "danceability": 0.648,
            "energy": 0.693,
            "valence": 0.959,
            "acousticness": 0.0851,
            "instrumentalness": 0.000000,
            "tempo": 120.043,
            "loudness": -4.359
        }
    },
    {
        "id": "1zHlj4dQ8ZAtrayhuDDmkY",
        "title": "Need You Now",
        "artist": "Lady Antebellum",
        "album": "Need You Now",
        "genres": ["country", "country pop"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273f9b8b5f60b6b2bb5f9b8b5f6",
        "audio_features": {
            "danceability": 0.567,
            "energy": 0.506,
            "valence": 0.284,
            "acousticness": 0.372,
            "instrumentalness": 0.000000,
            "tempo": 132.013,
            "loudness": -7.965
        }
    },
    
    # Alternative (2 songs)
    {
        "id": "7GhIk7Il098yCjg4BQjzvb",
        "title": "Radioactive",
        "artist": "Imagine Dragons",
        "album": "Night Visions",
        "genres": ["alternative", "rock"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273b83b446d40addb05b033e3ad",
        "audio_features": {
            "danceability": 0.593,
            "energy": 0.867,
            "valence": 0.334,
            "acousticness": 0.000081,
            "instrumentalness": 0.000002,
            "tempo": 136.040,
            "loudness": -4.464
        }
    },
    {
        "id": "1mea3bSkSGXuIRvnydlB5b",
        "title": "Pumped Up Kicks",
        "artist": "Foster the People",
        "album": "Torches",
        "genres": ["alternative", "indie pop"],
        "preview_url": "https://p.scdn.co/mp3-preview/...",
        "album_cover": "https://i.scdn.co/image/ab67616d0000b273f9b8b5f60b6b2bb5f9b8b5f6",
        "audio_features": {
            "danceability": 0.703,
            "energy": 0.622,
            "valence": 0.686,
            "acousticness": 0.011,
            "instrumentalness": 0.000105,
            "tempo": 127.851,
            "loudness": -6.958
        }
    }
]