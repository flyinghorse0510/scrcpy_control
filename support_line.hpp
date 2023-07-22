#include <cstdio>



class SupportLine
{
public:
    int _bufferPoint;
    int _bufferCount;
    int _supportPoint;
    int _minConfirmCount;
    SupportLine(int minConfirmCount = 3)
    {
        _bufferPoint = -1;
        _bufferCount = 0;
        _supportPoint = -1;
        _minConfirmCount = minConfirmCount;
    }

    void reset_support_line(void)
    {
        _bufferPoint = -1;
        _bufferCount = 0;
        _supportPoint = -1;
    }

    int update_support_line(int measurePoint)
    {
        if (measurePoint < 0)
        {
            return _supportPoint;
        }

        if (measurePoint < _supportPoint)
        {
            std::fprintf(stderr, "[SUPPORT LINE WARNING]: Support point: %d, Buffer point: %d, Buffer count: %d, Measure point: %d\n", _supportPoint, _bufferPoint, _bufferCount, measurePoint);
            std::fflush(stderr);
            return _supportPoint;
        }

        if (measurePoint == _supportPoint)
        {
            return _supportPoint;
        }

        if (_bufferCount == 0)
        {
            _bufferPoint = measurePoint;
            _bufferCount++;
            return _supportPoint;
        }

        if (measurePoint < _bufferPoint)
        {
            _bufferCount = 1;
            _bufferPoint = measurePoint;
            return _supportPoint;
        }

        if (measurePoint > _bufferPoint)
        {
            _supportPoint = _bufferPoint;
            _bufferPoint = measurePoint;
            _bufferCount = 1;
            return _supportPoint;
        }

        if (measurePoint == _bufferPoint)
        {
            if (_bufferCount == _minConfirmCount - 1)
            {
                _supportPoint = _bufferPoint;
                _bufferCount = 0;
            }
            else
            {
                _bufferCount++;
            }
            return _supportPoint;
        }

        std::fprintf(stdout, "[SUPPORT LINE FATAL ERROR]: Unbounded situation!\nSupport point: %d, Buffer point: %d, Buffer count: %d, Measure point: %d\n", _supportPoint, _bufferPoint, _bufferCount, measurePoint);
        std::fflush(stdout);
        return _supportPoint;
    }

    int get_support_point(void) {
        return _supportPoint;
    }
};