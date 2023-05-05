# Installing

> **Note** It is a good idea to use a virtual environment but here I will show an example without it for simplicity

First, we need to configure the bot via environment variables.
We will do this using the file `.env`

1. Rename file `.env.example` into `.env`
2. Fill out the file `.env`

Then, we need to install dependencies
```bash
pip install -r requirements.txt
```

Now everything is ready and we can launch the bot!

```bash
python3 run.py
```

> **Warning** If you see this error when trying to play something:
> 
> `ClientException: static_ffmpeg was not found.`
> 
> Then you need to add folder "**[python_dir]\Scripts**" into the **PATH**,
> or just install ffmpeg manually and change **FFMPEG_OPTIONS "executable"** to **"ffmpeg"**
> in the `settings.py` file
