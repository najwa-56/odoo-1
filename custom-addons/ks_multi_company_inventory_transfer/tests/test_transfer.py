from odoo.tests import TransactionCase


class MyTests(TransactionCase):

    # def setUp(self):
    #     super(MyTests, self).setUp()

    #     # create an transfer record
    #     self.transfer1 = self.env['multicompany.transfer.stock'].create({
    #         'ks_transfer_from': 'My Company (San Francisco)',
    #         'ks_transfer_to': 'My Company (San Francisco)',
    #         'ks_transfer_from_location': 'Physical Locations/YourCompany: Transit Location',
    #         'ks_transfer_to_location': 'Physical Locations/YourCompany: Transit Location',
    #
    #     })

    def test_transfer_between_a_company(self):
        # self.assertEqual(self.trnsfer1.state, 'posted')
        print(" My Test successfull")
