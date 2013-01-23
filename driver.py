#!/usr/bin/env python

import struct
import utils


class driver(object):
    @classmethod
    def encode(cls, fp):
        raise NotImplementedError("driver failed to implement %s" % (utils.get_caller_function_name()),)


    def decode(self, encoded_data):
        raise NotImplementedError("driver failed to implement %s" % (utils.get_caller_function_name()),)


class standard_driver(driver):
    def get_header(self, blob, end_padding_size=None):
        raise NotImplementedError("driver failed to implement %s" % (utils.get_caller_function_name()),)


    def get_end_padding_size(self, data, header_size):
        raise NotImplementedError("driver failed to implement %s" % (utils.get_caller_function_name()),)


    @classmethod
    def encode(cls, fp):
        driver = cls()

        data = fp.read()

        preliminary_header = driver.get_header(data)
        end_padding_size = driver.get_end_padding_size(data, len(preliminary_header))

        final_header = driver.get_header(data, end_padding_size)
        final_format = '!%ds%ds%dx' % (len(final_header), len(data), end_padding_size)

        assert(len(final_header) == len(preliminary_header))

        return struct.pack(final_format, final_header, data)


class versioned_driver(standard_driver):
    signature = 'IMGSTORE'
    registered_drivers = dict()

    def get_version_num(self):
        raise NotImplementedError("driver failed to implement %s" % (utils.get_caller_function_name()),)


    def get_version_specific_header(self, blob, return_empty_header=False):
        raise NotImplementedError("driver failed to implement %s" % (utils.get_caller_function_name()),)


    def decode_version_specific_header(self, header_data, version_specific_header):
        raise NotImplementedError("driver failed to implement %s" % (utils.get_caller_function_name()),)


    def get_header(self, blob, end_padding_size=None):
        return_empty_header = True if end_padding_size is None else False
        version_specific_header = self.get_version_specific_header(blob, return_empty_header)
        end_padding_size = 0 if end_padding_size is None else end_padding_size

        format_str = '!%dsIII%ds' % (len(versioned_driver.signature), len(version_specific_header),)

        return struct.pack(format_str, 
                           versioned_driver.signature,
                           self.get_version_num(),
                           len(version_specific_header),
                           end_padding_size,
                           version_specific_header)


    def decode(self, encoded_data):
        header_data = self.decode_header(encoded_data)

        return header_data, encoded_data[header_data['data_offset']:
                                         -header_data['end_padding_size']]


    def decode_header(self, encoded_data, skip_version_specific_header = False):
        format_str = '!%dsIII' % (len(versioned_driver.signature),)
        expected_length = struct.calcsize(format_str)

        partial_header = encoded_data[:expected_length]

        (signature, version_num,
         version_specific_header_length, end_padding_size) = struct.unpack(format_str,
                                                                           partial_header)

        assert (signature == versioned_driver.signature)

        header_data = {'signature': signature,
                       'version_num': version_num,
                       'data_offset': expected_length + version_specific_header_length,
                       'end_padding_size': end_padding_size,
                       }

        if (skip_version_specific_header):
            return header_data

        version_specific_header = encoded_data[expected_length:
                                               expected_length + version_specific_header_length]

        return self.decode_version_specific_header(header_data, version_specific_header)


    @staticmethod
    def infer_and_decode(encoded_data):
        header_decoder = versioned_driver()

        header = header_decoder.decode_header(encoded_data, True)

        driver = versioned_driver.registered_drivers[header['version_num']]()

        return driver.decode(encoded_data)


    @staticmethod
    def register_driver(version, driver):
        assert (version not in versioned_driver.registered_drivers)
        versioned_driver.registered_drivers[version] = driver


class v0_driver(versioned_driver):
    def get_version_num(self):
        return 0


    def get_version_specific_header(self, blob, return_empty_header=False):
        import hashlib
        hasher = hashlib.sha512()

        if (return_empty_header):
            return ' ' * hasher.digest_size

        hasher.update(blob)
        return hasher.digest()


    def decode_version_specific_header(self, header_data, version_specific_header):
        import hashlib
        hasher = hashlib.sha512()

        format_str = '!%ds' % (hasher.digest_size,)

        header_data['checksum'] = struct.unpack(format_str, version_specific_header)[0]

        return header_data


    def decode(self, encoded_data):
        header_data, decoded_data = super(v0_driver, self).decode(encoded_data)

        import hashlib
        hasher = hashlib.sha512()

        hasher.update(decoded_data)

        assert(hasher.digest() == header_data['checksum'])

        return (header_data, decoded_data)


    def get_end_padding_size(self, data, header_size):
        import math
        total_length = len(data) + header_size

        ceil = math.ceil(math.sqrt(float(total_length) / 16)) * 4
        assert(int(ceil) == ceil)
        assert(ceil - int(ceil) == 0)
        assert(ceil == int(float(ceil) / 4) * 4)
        return (ceil * ceil) - total_length


versioned_driver.register_driver(0, v0_driver)
