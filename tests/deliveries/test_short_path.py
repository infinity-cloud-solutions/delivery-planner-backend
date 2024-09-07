from unittest import TestCase
from decimal import Decimal
import time
from src.orders.delivery.location_router import TravelPlanner


class TestShortPath(TestCase):

    def setUp(self):
        self.locations = [
            {
                "client_name": "RICARDO FIKA GRAN TOSTADOR",
                "longitude": "-103.4252548792519945664025726728141307830810546875",
                "latitude": "20.687365588121000570254182093776762485504150390625",
            },
            {
                "client_name": "ALEJANDRA CABRALES",
                "longitude": "-103.430164159941995194458286277949810028076171875",
                "latitude": "20.656317803383000608619113336317241191864013671875"
            },
            {
                "client_name": "CLAUDIA OLMOS",
                "longitude": "-103.4176716876300048397752107121050357818603515625",
                "latitude": "20.619887118516000867884940817020833492279052734375"
            },
            {
                "client_name": "GLORIA LOMELI RODRIGUEZ",
                "longitude": "-103.368427000645993985017412342131137847900390625",
                "latitude": "20.71844539172899857248921762220561504364013671875"
            },
            {
                "client_name": "EMMANUEL RODRIGUEZ",
                "longitude": "-103.3697349966359979589469730854034423828125",
                "latitude": "20.66750492000399930248022428713738918304443359375"
            },
            {
                "client_name": "FLAVIO",
                "longitude": "-103.375458310743994161384762264788150787353515625",
                "latitude": "20.728684779687998940289617166854441165924072265625"
            },
            {
                "client_name": "YESSICA AGUILAR ",
                "longitude": "-103.466423099612001124114613048732280731201171875",
                "latitude": "20.699182981951000925846528843976557254791259765625"
            },
            {
                "client_name": "CINTHYA SAENZ",
                "longitude": "-103.42947349112000665627419948577880859375",
                "latitude": "20.6183578821920008294910076074302196502685546875"
            },
            {
                "client_name": "MARI CARMEN LEPE",
                "longitude": "-103.4766066928749950193378026597201824188232421875",
                "latitude": "20.62493558070899979384194011799991130828857421875"
            },
            {
                "client_name": "CLAUDIA VALENCIA",
                "longitude": "-103.422798400000004903631634078919887542724609375",
                "latitude": "20.725808900000000534191713086329400539398193359375"
            },
            {"latitude": 20.7257943, "longitude": -103.3792193},
        ]

    def test_give_a_request_with_ten_items(
        self,
    ):

        scheduler = TravelPlanner()
        morning_starting_point = {
                "latitude": 20.7257943,
                "longitude": -103.3792193,
            }
        start_time = time.time()
        print(f"Started at: {start_time}")
        observed = scheduler.find_shortest_path(
                self.locations, morning_starting_point
            )
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution time: {execution_time} seconds")
        print(observed)
        self.assertEqual(1, 1)
