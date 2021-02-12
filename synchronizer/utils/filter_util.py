class FilterUtil:

    @staticmethod
    def filter_ids_list(sync_ids, param_name, limit=100):
        filter_list = []
        counter = 0
        filter_param = ''
        for sync_id in sync_ids:
            filter_param += param_name + '=' + sync_id[0] + ';'
            counter += 1
            if counter >= limit:
                filter_list.append(filter_param)
                filter_param = ''
                counter = 0

        if filter_param != '':
            filter_list.append(filter_param)

        return filter_list
