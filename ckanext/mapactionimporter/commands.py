from ckantoolkit import CkanCommand
import paste.script

from ckanext.mapactionimporter.plugin import (
    create_product_themes
)


class MapactionImporterCommand(CkanCommand):
    """
    ckanext-mapactionimporter management commands

    Usage::
        paster mapactionimporter create_product_themes

    """
    summary = __doc__.split('\n')[0]
    usage = __doc__

    parser = paste.script.command.Command.standard_parser(verbose=True)
    parser.add_option('-c', '--config', dest='config',
                      default='development.ini',
                      help='Config file to use.')

    def command(self):
        cmd = None
        if self.args:
            cmd = self.args[0]

        self._load_config()

        if cmd == 'create_product_themes':
            create_product_themes
        else:
            print self.__doc__
