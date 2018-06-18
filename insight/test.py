import bokeh.sampledata
import os, pickle, pyDate
from bokeh.plotting import figure, output_file, show

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

if __name__ == '__main__':

    # with open('count.pickle') as f:
    #     count = pickle.load(f)[0]
    #
    # fyear = []
    # nobs  = []
    # for k in count.keys():
    #     year,doy = k.split('_')
    #     date = pyDate.Date(year=year,doy=doy)
    #     fyear.append(date.fyear)
    #     nobs.append(count[k])
    #
    # p = figure(plot_width=500, plot_height=500, tools="pan,reset,save,zoom_in,zoom_out")
    #
    # p.circle(fyear, nobs,alpha=0.5)
    # output_file("foo.html")
    # show(p)

    # count = {}
    #
    # for root, dir, files in os.walk("/Users/abelbrown/data/networks/g09/g09"):
    #     for f in files:
    #         file_name_parts = f.split('.')
    #         year = file_name_parts[1]
    #         doy  = file_name_parts[2]
    #         key = year+"_"+doy
    #         fpath = os.path.join(root,f)
    #         flen = file_len(fpath)
    #         if count.has_key(key):
    #             count[key]+=flen
    #         else:
    #             count[key] = flen
    #         #print fpath,flen,year, doy, count[key]
    #
    # with open('count.pickle', 'w') as f:
    #     pickle.dump([count], f)


    # create a Figure object
    #p = figure(plot_width=400, plot_height=400, tools="pan,reset,save,zoom_in")

    # add a Circle renderer to this figure
    #p.circle([1, 2, 3, 4], [1, 2, 3, 4], radius=[0.1,0.2,0.3,0.4], alpha=0.5)

    # specify how to output the plot(s)
    #output_file("foo.html")

    # display the figure
    #show(p)