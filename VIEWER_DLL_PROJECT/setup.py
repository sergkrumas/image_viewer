from distutils.core import setup, Extension

def main():
    setup(name="kiv_extensions",
          version="1.0.0",
          description="Python interface for C/C++ functions",
          author="Sergei Krumas",
          author_email="",
          ext_modules=[
                Extension('viewer_dll', ['viewer_dll.cc'], 
                            # extra_compile_args=['/utf-8'],
                            # extra_link_args=['/DEBUG']
                    )
        ],
    )

if __name__ == "__main__":
    main()
