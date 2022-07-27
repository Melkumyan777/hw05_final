from datetime import datetime


def year(request):
    curret_year = datetime.now().year
    return {
        'year': curret_year
    }
