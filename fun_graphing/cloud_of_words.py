from wordcloud import WordCloud
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

im_frame = Image.open('M:\GitRepositories\Discord-Scraper\scrapes\leon.png')
leon_np_frame = np.array(im_frame)
ignore_words = {'https', 'http', 'tenor', 'view', 'com', 'and', 'it'}

with open('../scrapes/messages_test.txt', 'r', encoding='utf-8') as f:
    wordcloud = WordCloud(
        width=1920,
        height=1080,
        margin=0,
        max_words=10000,
        scale=5,
        normalize_plurals=True,
        stopwords=ignore_words,
        background_color='#1d1e25',
        colormap='twilight',
        # mask=leon_np_frame
    ).generate(f.read())

    wordcloud.to_file('../scrapes/hamilton_leon_cloud.png')
    # Display the generated image:
    # plt.imshow(wordcloud, interpolation='bilinear')
    # plt.axis("off")
    # plt.margins(x=0, y=0)
    # plt.show()