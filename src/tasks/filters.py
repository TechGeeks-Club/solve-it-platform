from django.contrib.admin import SimpleListFilter


class TaskSolutionListFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = "My Tasks"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "f1"

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return [
            ("my", ("My Tasks Solution")),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # This filter is no longer used since manual correction tracking was removed
        return queryset
