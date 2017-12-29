import sys,os
Base=os.path.join(os.path.abspath(__file__),'..','..','..','..')
sys.path.append(os.path.abspath(Base))
print(sys.path)
if __name__=="__main__":
    from KnesetCrawler import main
    main(sys.argv)
