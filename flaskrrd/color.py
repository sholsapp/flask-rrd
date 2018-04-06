class ColorWheel(object):

    i = 0

    CRAFTSMAN = [
      '#d7c797', # (215,199,151)
      '#845422', # (132,84,34)
      '#ead61c', # (234,214,28)
      '#a47c48', # (164,124,72)
      '#000000', # (0,0,0)
    ]

    GRYFFINDOR = [
      '#740001', # (116,0,1)
      '#ae0001', # (174,0,1)
      '#eeba30', # (238,186,48)
      '#d3a625', # (211,166,37)
      '#000000', # (0,0,0)
    ]

    WHEEL = list(GRYFFINDOR)


    @classmethod
    def hex_to_rgb(cls, value):
        value = value.lstrip('#')
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

    @classmethod
    def rgb_to_hex(cls, rgb):
        return '#%02x%02x%02x' % rgb

    def next(self):
        color = self.WHEEL[self.i % len(self.WHEEL)]
        self.i += 1
        return color
