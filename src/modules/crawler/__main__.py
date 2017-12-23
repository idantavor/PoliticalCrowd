import sys,os
Base=os.path.join(os.path.abspath(__file__),'..','..','..')
sys.path.append(Base)
if __name__=="__main__":
    from KnesetCrawler import main
    main(sys.argv)
