import argparse
import io
import json
import sys

import maec2stix.translator

try:
    import stix2
except ImportError:
    stix2 = None


def main():
    parser = argparse.ArgumentParser(
        description="""
        Translates MAEC 5.0 packages to STIX 2.1 bundles.
        """
    )

    parser.add_argument("in",
                        help="""
                        Path to file with a MAEC package (as JSON) to
                        translate.  Use "-" to read from stdin.
                        """)
    parser.add_argument("-o",
                        help="""
                        Path to file to write the translated STIX to (as JSON).
                        (Default: write to stdout)
                        """,
                        metavar="OUT")
    parser.add_argument("-e",
                        help="""
                        Encoding to use for reading/writing files (Default:
                         %(default)s).  Does not apply to stdin/out.
                        """,
                        default="utf8",
                        metavar="ENCODING")

    parser.add_argument("-n",
                        help="""
                        Don't parse the translated STIX bundle using the stix2
                        library.  Only applicable when that library is
                        installed.  Otherwise, the option is ignored.
                        """,
                        action="store_true"
                        )

    args = parser.parse_args()

    in_ = out = None

    try:

        # "in" is a python keyword
        in_arg = getattr(args, "in")
        if in_arg == "-":
            in_ = sys.stdin
        else:
            in_ = io.open(in_arg, "r", encoding=args.e)

        maec_package = json.load(in_)

    finally:
        if in_ not in (None, sys.stdin):
            in_.close()

    try:

        if args.o:
            out = io.open(args.o, "w", encoding=args.e)
        else:
            out = sys.stdout

        if stix2 and not args.n:
            stix_bundle_object = \
                maec2stix.translator.translate_package_to_object(maec_package)
            out.write(stix_bundle_object.serialize(pretty=True))

        else:
            stix_bundle = maec2stix.translator.translate_package(maec_package)

            # Workaround for python2's dumb json.dump() implementation.  It
            # won't work with text streams.  But it's the "right" way to do it
            # (JSON is text, after all!), so I'd rather do it the right way,
            # with a workaround.  Using ensure_ascii=True and writing to a
            # binary stream would cause it to escape high-codepoint chars with
            # "\uXXXX" syntax, which I don't want.
            if sys.version_info.major >= 3:
                json.dump(stix_bundle, out, ensure_ascii=False, indent=4)
            else:
                out.write(json.dumps(stix_bundle, ensure_ascii=False, indent=4))

    finally:
        if out not in (None, sys.stdout):
            out.close()


if __name__ == "__main__":
    main()
