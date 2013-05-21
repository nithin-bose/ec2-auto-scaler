import logging


class LoadBalancers():

    def file_contents(self, filename=None, content=None):
        '''
        Just return the contents of a file as a string or write if content
        is specified. Returns the contents of the filename either way.
        '''
        if content is not None:
            logging.info('Writing to %s...' % filename)
            f = open(filename, 'w')
            f.write(content)
            f.close()

        try:
            logging.info('Reading from %s...' % filename)
            f = open(filename, 'r')
            text = f.read()
            f.close()
        except:
            text = None

        logging.info('Done')
        return text