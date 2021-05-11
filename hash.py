import hashlib


class hash:
  @staticmethod
  def calculate(seed):

    h = hashlib.sha512()
    h.update(seed.encode('utf-8'))

    return h.hexdigest()
