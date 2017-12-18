from haystack import indexes

from player.models import Player


class PlayerIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.EdgeNgramField(document=True, use_template=True)

    def get_model(self):
        return Player

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
