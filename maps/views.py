from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import LocationForm
from .models import Location


# Create your views here.
def map_view(request, pk):
    location = get_object_or_404(Location, pk=pk)
    is_gm = location.world.creator == request.user
    user_id = request.user.id
    return render(request, "maps/map_view.html", {"location": location, "is_gm": is_gm, "user_id": user_id})


class LocationCreateView(CreateView):
    model = Location
    form_class = LocationForm
    template_name = 'maps/location_form.html'

    def get_initial(self):
        initial = super().get_initial()
        world_id = self.kwargs.get('world_id')
        if world_id:
            initial['world'] = world_id
        return initial

    def form_valid(self, form):
        world_id = self.kwargs.get('world_id')
        if world_id:
            form.instance.world_id = world_id
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['world_id'] = self.kwargs.get('world_id')
        return ctx

    def get_success_url(self):
        return reverse('worlds:detail', args=[self.object.world.pk])


class LocationUpdateView(UpdateView):
    model = Location
    fields = ['name', 'description', 'image', 'is_opened']
    template_name = 'maps/location_form.html'

    def get_initial(self):
        initial = super().get_initial()
        world_id = self.kwargs.get('world_id')
        if world_id:
            initial['world'] = world_id
        return initial

    def form_valid(self, form):
        world_id = self.kwargs.get('world_id')
        if world_id:
            form.instance.world_id = world_id
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['world_id'] = self.kwargs.get('world_id')
        ctx['update'] = True
        return ctx

    def get_success_url(self):
        return reverse('worlds:detail', args=[self.object.world.pk])


class LocationDeleteView(DeleteView):
    model = Location
    template_name = 'maps/location_confirm_delete.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['world_id'] = self.object.world.id
        return ctx

    def get_success_url(self):
        return reverse('worlds:detail', args=[self.object.world.pk])
