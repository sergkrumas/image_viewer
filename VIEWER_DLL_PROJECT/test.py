





import time
import viewer_dll

def main():

    for n in reversed(range(4)):
        if n == 0:
            continue
        print(f'{n}...')
        time.sleep(1.0)

    func_out = viewer_dll.getFileListFromExplorerWindow(fullpaths=True)

    print("elements count is: ", len(func_out))
    for filename in func_out:
        print("\t", filename)

    input('press any key to exit...')

if __name__ == '__main__':
    main()


