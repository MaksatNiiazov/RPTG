from django.shortcuts import render, get_object_or_404

from maps.models import Location


# Create your views here.
def map_view(request, pk):
    location = get_object_or_404(Location, pk=pk)
    return render(request, "maps/map_view.html", {"location": location})